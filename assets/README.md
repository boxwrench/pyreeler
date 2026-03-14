# Assets

This folder contains media assets for the PyReeler repository.

## Structure

```
assets/
├── logo/           # PyReeler logo and branding assets
│   ├── logo.png
│   ├── logo-dark.png
│   └── logo.svg
│
└── showcase/       # Featured example films and loops
    ├── horizon-maintenance-log.mp4
    └── *.mp4, *.png posters
```

## Logo

The PyReeler logo and branding assets live here. Use these for:
- Repository social preview
- Documentation headers
- External project references

## Showcase

Featured code-generated films, loops, and experimental motion pieces made with PyReeler.

Each showcase piece should include:
- The final video (`.mp4` preferred)
- A poster/thumbnail image (`.png`, ~1280x720)
- Optional: brief description of the piece

Current featured showcase files include:
- `pyreeler-emergence.mp4`
- `what-the-light-kept_preview.mp4`

Benchmark notes, renderer scripts, and effect catalogs should live in the repository `examples/` folder rather than inside `assets/showcase/`.

## Research

The `assets/` directory may also contain design and research documents used while developing the skill, such as:
- `Code-Generated Film Design Space.docx`
- `Generative Audio Pipeline Design.docx`
- `Hardware-Aware AI Video Tool.docx`

## Repository Examples

See root `examples/` folder for sample films and loops created with PyReeler.
