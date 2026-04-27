---
name: frevana-gen-image
description: Generate images through Frevana and return the generated image URL plus response metadata. Use this whenever the user wants to create an image from a prompt with Frevana, mentions `generate-image`, asks for `gpt-image` or Gemini image generation through Frevana, or needs a hosted image URL returned from the backend.
---

# Frevana Image Generator

Generate images by calling Frevana's `POST https://api-report.frevana.com/report/generate-image`.

## Purpose

This skill is for **backend image generation** through Frevana.

Inputs:
- `prompt`
- `provider`
- `model`
- optional `quality`
- optional `size`

Output:
- response JSON containing `image_url`, `provider`, `model`, and `credits_consumed`

Treat `image_url` as the primary generated asset URL. Do not rewrite, proxy, or transform it unless the user explicitly asks for that.

## What This Skill Needs

- user-provided `prompt`
- user-provided `provider`
- user-provided `model`
- optional `quality` and `size`
- `FREVANA_TOKEN` in the environment, or an explicit `--token` override for the current run
- `curl`
- `bash`
- `python3`

## Execution Order

Use this flow so the request stays simple and reliable:

1. Confirm the user has provided `prompt`, `provider`, and `model`.
2. Validate that the model matches the selected provider.
3. Send `quality` and `size` whenever the user provides them and the values pass validation.
4. Prefer the script over ad hoc `curl` commands.
5. Let the script read `FREVANA_TOKEN` first.
6. In interactive shell usage, if `FREVANA_TOKEN` is missing, the script may prompt for it.
7. In non-interactive or agent workflows, fail fast if the token is missing and tell the user to set `FREVANA_TOKEN` or pass `--token` explicitly.
8. Parse the response JSON and verify `image_url`, `provider`, `model`, and `credits_consumed`.
9. Return the response JSON as the final API result. If the user only wants the image URL, return `image_url`.
10. When useful, also save the JSON response to a file.

## Allowed Values

### Providers

- `openai`
- `gemini`

### Models

#### OpenAI models

- `gpt-image-1.5`
- `gpt-image-2`

#### Gemini models

- `gemini-3-pro-image-preview`
- `gemini-3.1-flash-image-preview`

### Quality

- `standard`
- `hd`
- `low`
- `medium`
- `high`
- `auto`

### Size

- `auto`
- `1024x1024`
- `1536x1024`
- `1024x1536`
- `256x256`
- `512x512`
- `1792x1024`
- `1024x1792`

## Commands

### Minimal request

```bash
bash <skill-path>/scripts/generate_image.sh \
  --prompt "A cinematic product shot of a matte black espresso machine on travertine" \
  --provider openai \
  --model gpt-image-2
```

### OpenAI request with quality and size

```bash
bash <skill-path>/scripts/generate_image.sh \
  --prompt "An editorial cover illustration about AI agents in finance, warm paper collage style" \
  --provider openai \
  --model gpt-image-1.5 \
  --quality high \
  --size 1536x1024
```

### Gemini request with quality and size

```bash
bash <skill-path>/scripts/generate_image.sh \
  --prompt "A playful isometric dashboard scene with charts floating above a desk" \
  --provider gemini \
  --model gemini-3.1-flash-image-preview \
  --quality high \
  --size 1024x1024
```

### Save returned JSON to a file

```bash
bash <skill-path>/scripts/generate_image.sh \
  --prompt "A hyperreal skincare product photo with translucent water splash" \
  --provider openai \
  --model gpt-image-2 \
  --quality hd \
  --size 1024x1024 \
  --output ./out/generated-image.json
```

### Token override for the current run

Use a token override only when the user explicitly gives one for the current run.

```bash
bash <skill-path>/scripts/generate_image.sh \
  --prompt "A clean SaaS hero illustration with bold geometric forms" \
  --provider gemini \
  --model gemini-3-pro-image-preview \
  --token "your bearer token"
```

## Fixed Request Shape

The script sends this payload shape:

```json
{
  "prompt": "image generation prompt",
  "provider": "openai",
  "model": "gpt-image-2",
  "quality": "high",
  "size": "1024x1024"
}
```

`quality` and `size` are omitted unless they are explicitly provided.

## Response Shape

The API response is expected to be JSON like:

```json
{
  "image_url": "https://static.frevana.com/images/xxx.png",
  "provider": "openai",
  "model": "gpt-image-2",
  "credits_consumed": 0
}
```

This skill validates those fields and returns that JSON object.

## Output

- Success: the script parses the response JSON, validates the key fields, and prints normalized JSON to stdout
- With `--output`: the same JSON is also written to the specified file path
- Failure: the script prints the response body or parsing error and exits non-zero
- `image_url` is the primary generated result and should be surfaced clearly in the final answer

## Notes

- Require `--prompt`, `--provider`, and `--model`
- `--quality` and `--size` are valid for both `openai` and `gemini`
- Reject mismatched provider and model combinations
- If `curl` is missing, stop and tell the user to install `curl`
- If `bash` is unavailable, stop and tell the user to run the script in a Bash environment
- Do not echo the Bearer token back to the user
- Keep prompts as plain text and pass them through unchanged unless the user asks for prompt rewriting

## Example Prompts

### Chinese

- "调用 Frevana 的 `/report/generate-image`，prompt 是这段产品海报描述，provider 用 `openai`，model 用 `gpt-image-2`"
- "帮我走 Frevana 图片生成接口，生成一张 AI 金融主题插图，返回图片 URL"
- "用 `gemini-3-pro-image-preview` 按这个 prompt 出图，带上 `quality=high` 和 `size=1024x1024`，把返回 JSON 保存下来"
- "我给你 prompt、provider 和 model，你帮我调 Frevana 后端图片生成 API"

### English

- "Call Frevana `/report/generate-image` with this prompt and return the hosted image URL"
- "Generate an image through Frevana using `openai` and `gpt-image-2`, high quality, square format"
- "Use Frevana with Gemini image preview to create a dashboard illustration and save the JSON response"
- "Given a prompt, provider, and model, call the Frevana backend image API and return the result metadata"
