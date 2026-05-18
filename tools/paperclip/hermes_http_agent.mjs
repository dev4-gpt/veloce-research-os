#!/usr/bin/env node

const DEFAULT_BASE_URL = "http://hermes:8642/v1";
const DEFAULT_MODEL = "hermes-agent";
const DEFAULT_TIMEOUT_MS = 180000;

function env(name, fallback = "") {
  const value = process.env[name];
  return value && value.trim() ? value.trim() : fallback;
}

function maskUrl(url) {
  try {
    const parsed = new URL(url);
    return `${parsed.protocol}//${parsed.host}${parsed.pathname}`;
  } catch {
    return "invalid-url";
  }
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data.trim()));
    process.stdin.on("error", reject);
  });
}

function buildPrompt(stdinPrompt) {
  const argPrompt = process.argv.slice(2).join(" ").trim();
  const prompt = stdinPrompt || argPrompt;
  if (!prompt) {
    throw new Error("No prompt provided on stdin or as command arguments.");
  }
  return prompt;
}

function buildRequestBody(prompt, model) {
  return {
    model,
    messages: [
      {
        role: "system",
        content: [
          "You are Veloce Hermes HTTP Agent.",
          "Answer the assigned Paperclip issue directly.",
          "If the task is complete, include a short disposition recommendation.",
          "Do not claim that you modified Paperclip state unless the prompt includes tool output proving it.",
        ].join(" "),
      },
      {
        role: "user",
        content: prompt,
      },
    ],
  };
}

function getResponseText(payload) {
  const choice = payload?.choices?.[0];
  const content = choice?.message?.content;
  if (typeof content === "string" && content.trim()) {
    return content.trim();
  }
  throw new Error("Hermes response did not include choices[0].message.content.");
}

function timeoutSignal(timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  return { signal: controller.signal, clear: () => clearTimeout(timeout) };
}

async function callHermes({ prompt, baseUrl, apiKey, model, timeoutMs }) {
  const endpoint = `${baseUrl.replace(/\/+$/, "")}/chat/completions`;
  const timer = timeoutSignal(timeoutMs);
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildRequestBody(prompt, model)),
      signal: timer.signal,
    });

    const text = await response.text();
    let payload;
    try {
      payload = text ? JSON.parse(text) : {};
    } catch {
      throw new Error(`Hermes returned non-JSON HTTP ${response.status}: ${text.slice(0, 240)}`);
    }

    if (!response.ok) {
      const message = payload?.error?.message || payload?.message || "unknown Hermes API error";
      throw new Error(`Hermes HTTP ${response.status}: ${message}`);
    }

    return {
      endpoint,
      response: getResponseText(payload),
      usage: payload?.usage || null,
    };
  } finally {
    timer.clear();
  }
}

function printSuccess({ model, baseUrl, result }) {
  console.log("# Hermes HTTP Agent Result");
  console.log("");
  console.log("Status: success");
  console.log(`Model: ${model}`);
  console.log(`Endpoint: ${maskUrl(result.endpoint || baseUrl)}`);
  if (result.usage) {
    console.log(`Usage: ${JSON.stringify(result.usage)}`);
  }
  console.log("");
  console.log(result.response);
}

function printFailure(error, { model, baseUrl }) {
  console.error("# Hermes HTTP Agent Result");
  console.error("");
  console.error("Status: failed");
  console.error(`Model: ${model}`);
  console.error(`Endpoint: ${maskUrl(baseUrl)}`);
  console.error(`Error: ${error.message}`);
}

async function main() {
  const baseUrl = env("HERMES_BASE_URL", DEFAULT_BASE_URL);
  const apiKey = env("HERMES_API_KEY") || env("API_SERVER_KEY");
  const model = env("HERMES_MODEL", DEFAULT_MODEL);
  const timeoutMs = Number(env("HERMES_TIMEOUT_MS", String(DEFAULT_TIMEOUT_MS)));

  try {
    if (!apiKey) {
      throw new Error("Missing HERMES_API_KEY or API_SERVER_KEY.");
    }
    if (!Number.isFinite(timeoutMs) || timeoutMs < 1000) {
      throw new Error("HERMES_TIMEOUT_MS must be a number >= 1000.");
    }
    const prompt = buildPrompt(await readStdin());
    const result = await callHermes({ prompt, baseUrl, apiKey, model, timeoutMs });
    printSuccess({ model, baseUrl, result });
  } catch (error) {
    printFailure(error, { model, baseUrl });
    process.exitCode = 1;
  }
}

await main();
