# Video Generator Skill

## Purpose
Generate AI videos with 40+ models via inference.sh `belt` CLI (Veo 3.1, Seedance 2.0, HappyHorse 1.0, Wan 2.5, Grok Imagine, OmniHuman, Fabric, HunyuanVideo). Caps: text-to-video, image-to-video, reference-to-video, video editing, lipsync, avatar animation, upscaling, foley.

## Entry Point
```bash
uv run --no-sync python -m agent.skills.video_generator.run <repository-root>
# Direct belt usage:
belt login
belt app run google/veo-3-1-fast --input '{"prompt": "drone shot flying over a forest"}'
```

## Tools
- `generate` — Text-to-video via belt app (Veo, HappyHorse T2V, Seedance T2V)
- `image_to_video` — Animate image to video (Wan 2.5, Seedance I2V, HappyHorse I2V/R2V)
- `avatar` — Lipsync/avatar animation (OmniHuman, Fabric, PixVerse)
- `edit` — Natural language video editing (HappyHorse Edit)
- `upscale` — Video upscaling (Topaz)
- `foley` — Add sound effects (HunyuanVideo Foley)
- `merger` — Merge clips with transitions (Media Merger)

## Output
- `ArtifactRef` to generated video (contract `video_record`, v1.0)
- Execution evidence: `belt` run ID, model, duration, resolution, pre/post digests
- Disposition: `completed` / `blocked` (missing belt auth) / `not_run`

## Ownership
Runtime-authorized media generation, scoped to `bearer`-auth belt calls. Never fabricates video bytes; all output is belt-reported evidence.

## Responsibilities
- Text-to-video with audio (Seedance 2.0 `generate_audio`, Veo 3 audio)
- Image-to-video with camera motion and sync audio
- Avatar/lipsync from image+audio pairs
- Video edit via prompt, foley sound addition, upscaling

## Tools

| Tool | Inputs | Outputs |
|------|--------|---------|
| `generate` | prompt, model, duration, resolution, generate_audio | `VideoResult` with belt execution evidence |
| `image_to_video` | image_url, prompt, model | `VideoResult` |
| `avatar` | image_url, audio_url, model | `VideoResult` |
| `edit` | video_url, prompt, model | `VideoResult` |
| `upscale` | video_url, target | `VideoResult` |
| `foley` | video_url, prompt | `VideoResult` |
| `merger` | videos[], transition | `VideoResult` |

## Runtime Integration
- Reports through `HostDispatchResult` with `video_record` contract
- Never issues trusted receipts; host validates belt `artifact_digest`
- Host binds approval for outbound belt calls (default_deny)

## Constraints
- Requires `belt login` (INFERENCE_SH token) — without it, disposition `blocked`
- No whole-repository read; only explicit prompt/image/audio URLs
- Generated video bytes remain in inference.sh; host persists only ArtifactRef + digests
- Max duration/resolution per model table in references/models.md
