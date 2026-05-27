---
name: generating-image-prompts
description: Generates prompts for AI image generation tools (Midjourney, DALL-E, Stable Diffusion, Gemini). Use when creating prompts for architecture, interior design, floor plans, room visualizations, portraits, fashion photography, or any image generation. Supports direct description input, Pinterest board/image analysis, and iterative prompt refinement.
---

# Generating Image Prompts

Generate effective prompts for AI image generation tools.

## Quick Start

### From Description

1. Gather key details from user: room type, style preferences, key features
2. Build prompt using the structure: **Subject + Composition + Location + Style + Atmosphere**
3. Add photography/rendering style at the end
4. Output plain text prompt only

### From Pinterest Analysis

1. Fetch the Pinterest board/pin URL
2. Identify common themes: styles, materials, colors, lighting, compositions
3. Extract key visual patterns across multiple pins
4. Synthesize findings into a cohesive prompt that captures the essence

### Iterative Workflow

1. Provide initial prompt as plain text ready to copy/paste
2. User generates image and requests changes
3. Provide updated prompt incorporating the changes
4. Track all changes across iterations
5. When user asks for "full prompt", provide the complete accumulated version

## Prompt Formula

### Core Elements (required)

```
[Subject] + [Composition] + [Environment] + [Style] + [Photography type]
```

### Enhanced Elements (for professional results)

```
[Subject] + [Composition] + [Environment] + [Lighting] + [Materials] + [Atmosphere] + [Style] + [Photography type]
```

## Key Principles

1. **Keep it concise**: Short, clear phrases work better than long descriptions
2. **Be specific**: Use precise words ("herringbone oak floor" not "wood floor")
3. **Use specific numbers**: "three windows" not "windows"
4. **Focus on what you want**: Describe desired elements, not what to avoid
5. **Choose strong synonyms**: "expansive" instead of "big", "intimate" instead of "small"

## Output Format

- Plain text only, no parameters
- Single paragraph, comma-separated elements
- End with photography/rendering style
- No quotes around the prompt

## References

- [Prompt Structure](references/prompt-structure.md) - Detailed anatomy of effective prompts
- [Architecture](references/architecture.md) - Vocabulary for exterior and floor plans
- [Interior Design](references/interior-design.md) - Vocabulary for rooms, styles, materials
- [Portraits](references/portraits.md) - Cropping, poses, and lighting for portrait photography
