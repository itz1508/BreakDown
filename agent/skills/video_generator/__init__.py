"""Video Generator skill — AI video generation via belt CLI.

Ownership:
    Media generation via inference.sh belt, scoped to authenticated
    belt app run calls. The skill never fabricates bytes; all outputs
    are belt-reported evidence bound to ArtifactRef.

Tools:
    generate — text-to-video (Veo 3.1, HappyHorse T2V, Seedance T2V)
    image_to_video — animate image (Wan 2.5, Seedance I2V)
    avatar — lipsync/avatar (OmniHuman, Fabric)
    edit — natural language edit (HappyHorse Edit)
    upscale — Topaz upscaling
    foley — HunyuanVideo Foley

Runtime integration:
    Results via HostDispatchResult (contract video_record). Host
    validates belt artifact_digest and issues receipts.
"""

from agent.skills.video_generator.run import post_dispatch, pre_dispatch

__all__ = ["post_dispatch", "pre_dispatch"]
