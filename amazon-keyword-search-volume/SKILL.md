---
name: amazon-keyword-search-volume
description: Get Amazon keyword search volume via `skillpack-cli amazon search-volume`. Use whenever the user wants Amazon keyword demand, search-volume estimates, batch keyword lookups, or keyword research for Amazon SEO/PPC/listing decisions.
---

# Amazon Keyword Search Volume

Retrieve Amazon keyword search volume for one or more keywords through `skillpack-cli`.

## Execution Order

Use this order so the workflow stays fast:

1. Extract the keyword list plus any location/language hints from the user.
2. If the user does not provide location or language, default to `United States / English`. In the user-facing response, explicitly say that this default was used and tell them they can switch by naming a supported marketplace, such as `Australia` or `Germany`.
3. Run the target command directly. Do not pre-check `skillpack-cli` or `npm` before the first attempt.
4. If the command fails because `skillpack-cli` is missing, install it with:

```bash
npm install -g @cremini/skillpack-cli
```

5. After installation, rerun the same `skillpack-cli amazon search-volume ...` command.
6. If installation fails because `npm` is missing, stop and tell the user that Node.js/npm must be installed first.
7. If the command fails because login or credentials are missing, stop and tell the user to run `skillpack-cli login`, then retry.

## Commands

```bash
skillpack-cli amazon search-volume --keywords "wireless earbuds,gaming headset" --location-name "United States" --language-name "English"
skillpack-cli amazon search-volume --keywords "wireless earbuds,gaming headset" --location-name "Australia" --language-name "English"
skillpack-cli amazon search volume --keywords "wireless earbuds,gaming headset" --location-name "United States" --language-name "English"
```

## Output

`skillpack-cli` returns the Amazon keyword search volume payload to stdout as JSON. If the keyword list is empty, the user supplies an unsupported marketplace/language pair, or auth is missing, it returns an error on stderr with a non-zero exit code.

## Usage Notes

- If the user does not specify marketplace/language, default to `United States / English`.
- In the response, state the default explicitly. Example: `I used United States / English by default. If you want a different marketplace, tell me something like Australia, Germany, or United Kingdom.`
- Accept user inputs as either marketplace names or codes. If they give a supported marketplace name, map it to the approved code/language pair below.
- `--keywords` must be a comma-separated list. Trim whitespace and preserve the user-supplied phrases.
- Start with `skillpack-cli amazon search-volume ...` immediately instead of doing a separate availability check first.
- Only run the install command when the command output shows that `skillpack-cli` is missing.
- If `npm` is unavailable when installation is needed, stop and tell the user to install Node.js and npm first.
- If the command reports that the user is not logged in, authorization failed, or credentials are missing, stop and tell the user to run `skillpack-cli login`.
- If the user asks for a marketplace outside the supported list below, stop and say that this skill currently supports only the listed marketplaces.
- Summarize the highest- and lowest-volume keywords, and call out obvious gaps or opportunities when the user is doing keyword research.

## Supported Marketplaces

Use only these location/language pairs for this skill:

| Marketplace | location_code | language_code |
|-------------|---------------|---------------|
| Australia | 2036 | en |
| Austria | 2040 | de |
| Canada | 2124 | en |
| Egypt | 2818 | ar |
| France | 2250 | fr |
| Germany | 2276 | de |
| India | 2356 | en |
| Italy | 2380 | it |
| Mexico | 2484 | es |
| Netherlands | 2528 | nl |
| Saudi Arabia | 2682 | ar |
| Singapore | 2702 | en |
| Spain | 2724 | es |
| United Arab Emirates | 2784 | ar |
| United Kingdom | 2826 | en |
| United States | 2840 | en |

When users specify marketplace names, map them as follows:

- `Australia` -> `--location-code 2036 --location-name "Australia" --language-code en --language-name "English"`
- `Austria` -> `--location-code 2040 --location-name "Austria" --language-code de --language-name "German"`
- `Canada` -> `--location-code 2124 --location-name "Canada" --language-code en --language-name "English"`
- `Egypt` -> `--location-code 2818 --location-name "Egypt" --language-code ar --language-name "Arabic"`
- `France` -> `--location-code 2250 --location-name "France" --language-code fr --language-name "French"`
- `Germany` -> `--location-code 2276 --location-name "Germany" --language-code de --language-name "German"`
- `India` -> `--location-code 2356 --location-name "India" --language-code en --language-name "English"`
- `Italy` -> `--location-code 2380 --location-name "Italy" --language-code it --language-name "Italian"`
- `Mexico` -> `--location-code 2484 --location-name "Mexico" --language-code es --language-name "Spanish"`
- `Netherlands` -> `--location-code 2528 --location-name "Netherlands" --language-code nl --language-name "Dutch"`
- `Saudi Arabia` -> `--location-code 2682 --location-name "Saudi Arabia" --language-code ar --language-name "Arabic"`
- `Singapore` -> `--location-code 2702 --location-name "Singapore" --language-code en --language-name "English"`
- `Spain` -> `--location-code 2724 --location-name "Spain" --language-code es --language-name "Spanish"`
- `United Arab Emirates` -> `--location-code 2784 --location-name "United Arab Emirates" --language-code ar --language-name "Arabic"`
- `United Kingdom` -> `--location-code 2826 --location-name "United Kingdom" --language-code en --language-name "English"`
- `United States` -> `--location-code 2840 --location-name "United States" --language-code en --language-name "English"`

When showing examples or follow-up guidance to the user, prefer marketplace names instead of codes. Good examples:

- `Use Australia / English instead`
- `Run this for Germany`
- `Check the same keywords in United Kingdom`

## Follow-Up Questions

- "Check Amazon search volume for **wireless earbuds, gaming headset** in the **United States** in **English**"
- "Get Amazon keyword demand for **collagen peptides, grass fed collagen** in **Australia**"
- "Get Amazon keyword demand for **dish drying rack, over sink dish rack, compact dish rack**"
- "Run Amazon search-volume for **protein shaker bottle, blender bottle** in **United States**"
- "Compare search volume for these Amazon keywords before I decide which one to target"
