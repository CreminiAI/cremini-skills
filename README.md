# Cremini Skills

Open-source AI agent skills for [SkillPack](https://github.com/CreminiAI/skillpack).

## Skills

| Skill | Description |
|-------|-------------|
| [amazon-product](amazon-product/) | Fetch Amazon product details by ASIN |
| [amazon-search](amazon-search/) | Search Amazon products by keyword |
| [amazon-keyword-search-volume](amazon-keyword-search-volume/) | Get Amazon keyword search volume for one or more keywords |
| [notion](notion/) | Search, read, create, and manage Notion pages and databases |
| [web-fetch](web-fetch/) | Fetch web pages via Chrome DevTools Protocol — JS rendering, zero dependencies |

## Quick Start

Reference any skill in your `skillpack.json`:

```json
{
  "skills": [
    {
      "name": "notion",
      "source": "https://github.com/CreminiAI/cremini-skills",
      "description": "Manage Notion pages and databases through conversation."
    }
  ]
}
```

## License

MIT
