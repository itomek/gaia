# Features

Currently, the following capabilities are available, more will be added in the near future:

| Use-Case Example   | Function                                 | Description                                                     |
| ------------------ | ---------------------------------------- | --------------------------------------------------------------- |
| LLM Direct         | Direct LLM queries via CLI               | Direct model interaction using the new `gaia-cli llm` command  |
| Blender Agent      | 3D content creation and manipulation     | Specialized agent for Blender automation and workflow          |

## LLM Direct Usage

The `gaia-cli llm` command provides direct access to language models without requiring server setup. This is the simplest way to interact with AI models:

```bash
# Basic query
gaia-cli llm "What is 1+1?"

# Specify model and token limit
gaia-cli llm "Explain quantum computing" --model Llama-3.2-3B-Instruct-Hybrid --max-tokens 200

# Disable streaming for batch processing
gaia-cli llm "Write a short poem" --no-stream
```

**Requirements**: Requires lemonade-server to be running. The command will provide helpful error messages if the server is not accessible.

## Blender Agent

The Blender agent provides specialized functionality for 3D content creation and workflow automation. For more details, see the Blender agent documentation.

## Supported LLMs

The following is a list of the currently supported LLMs with GAIA using Ryzen AI Hybrid (NPU+iGPU) mode using `gaia-windows-setup.exe`. To request support for a new LLM, please contact the [AMD GAIA team](mailto:gaia@amd.com).

| LLM                    | Checkpoint                                                            | Backend            | Data Type |
| -----------------------|-----------------------------------------------------------------------|--------------------|-----------|
| Phi-3.5 Mini Instruct  | amd/Phi-3.5-mini-instruct-awq-g128-int4-asym-fp16-onnx-hybrid         | oga                | int4      |
| Phi-3 Mini Instruct    | amd/Phi-3-mini-4k-instruct-awq-g128-int4-asym-fp16-onnx-hybrid        | oga                | int4      |
| Llama-2 7B Chat        | amd/Llama-2-7b-chat-hf-awq-g128-int4-asym-fp16-onnx-hybrid            | oga                | int4      |
| Llama-3.2 1B Instruct  | amd/Llama-3.2-1B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid         | oga                | int4      |
| Llama-3.2 3B Instruct  | amd/Llama-3.2-3B-Instruct-awq-g128-int4-asym-fp16-onnx-hybrid         | oga                | int4      |
| Qwen 1.5 7B Chat       | amd/Qwen1.5-7B-Chat-awq-g128-int4-asym-fp16-onnx-hybrid               | oga                | int4      |
| Mistral 7B Instruct    | amd/Mistral-7B-Instruct-v0.3-awq-g128-int4-asym-fp16-onnx-hybrid      | oga                | int4      |

The following is a list of the currently supported LLMs in the generic version of GAIA (GAIA_Installer.exe). To request support for a new LLM, please contact the [AMD GAIA team](mailto:gaia@amd.com).
| LLM                    | Checkpoint                                                            | Device   | Backend            | Data Type |
| -----------------------|-----------------------------------------------------------------------|----------|--------------------|-----------|

* oga - [Onnx Runtime GenAI](https://github.com/microsoft/onnxruntime-genai)

# License

[MIT License](../LICENSE.md)

Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
SPDX-License-Identifier: MIT