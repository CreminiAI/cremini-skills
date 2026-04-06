# Cremini Skills

Open-source AI agent skills for [SkillPack](https://github.com/CreminiAI/skillpack).

## Skills

| Skill | Description |
|-------|-------------|
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
