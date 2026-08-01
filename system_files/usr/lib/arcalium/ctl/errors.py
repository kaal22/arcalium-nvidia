"""Documented Arcalium error codes (PRODUCT_SPEC §22)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArcError:
    code: str
    message: str
    exit_code: int = 1


# Command / schema errors
ARC_CMD_001 = ArcError("ARC-CMD-001", "Unknown command", 2)
ARC_CMD_002 = ArcError("ARC-CMD-002", "Command not implemented yet", 3)
ARC_CMD_003 = ArcError("ARC-CMD-003", "Invalid arguments", 2)

# GPU
ARC_GPU_001 = ArcError("ARC-GPU-001", "NVIDIA GPU not detected")
ARC_GPU_002 = ArcError("ARC-GPU-002", "NVIDIA module not loaded")
ARC_GPU_003 = ArcError("ARC-GPU-003", "Software rendering detected")
ARC_GPU_004 = ArcError("ARC-GPU-004", "Unexpected nouveau/NVK driver in use")

# Vulkan
ARC_VLK_001 = ArcError("ARC-VLK-001", "Vulkan unavailable")
ARC_VLK_002 = ArcError("ARC-VLK-002", "Vulkan has no NVIDIA device")

# Tooling
ARC_TOOL_001 = ArcError("ARC-TOOL-001", "Required diagnostic tool missing or failed")
ARC_TOOL_002 = ArcError("ARC-TOOL-002", "Diagnostic tool timed out")

# Network / Proton / Apps
ARC_NET_001 = ArcError("ARC-NET-001", "Network request failed")
ARC_PROTON_001 = ArcError("ARC-PROTON-001", "Proton install failed")
ARC_APPS_001 = ArcError("ARC-APPS-001", "Application operation failed")
ARC_APPS_002 = ArcError("ARC-APPS-002", "Application id not in catalogue")

# Local AI (Ollama)
ARC_AI_001 = ArcError("ARC-AI-001", "Ollama is not installed")
ARC_AI_002 = ArcError("ARC-AI-002", "Pinned AI model is not installed")
ARC_AI_003 = ArcError("ARC-AI-003", "Local AI session failed to launch")
