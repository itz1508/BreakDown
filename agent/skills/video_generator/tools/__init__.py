"""Video Generator tools — belt CLI wrappers.

Each tool maps to a belt app ID. Execution is host-authorized;
tools return evidence, never self-authorize.
"""

from agent.skills.video_generator.tools.avatar import run_avatar
from agent.skills.video_generator.tools.edit import run_edit
from agent.skills.video_generator.tools.foley import run_foley
from agent.skills.video_generator.tools.generate import run_generate
from agent.skills.video_generator.tools.image_to_video import run_image_to_video
from agent.skills.video_generator.tools.upscale import run_upscale

__all__ = ["run_avatar", "run_edit", "run_foley", "run_generate", "run_image_to_video", "run_upscale"]
