#!/bin/bash
# Script for converting models to MLX format with quantization
# Created: April 2025

# Text formatting
BOLD="\033[1m"
BLUE="\033[34m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}=====================================${RESET}"
echo -e "${BOLD}${BLUE}   MLX Model Conversion Utility      ${RESET}"
echo -e "${BOLD}${BLUE}=====================================${RESET}"
echo -e "This script generates the command to convert your model to MLX format\n"

# Default values
DEFAULT_HF_PATH="unsloth/Llama-3-1-ultra"
DEFAULT_OUTPUT_DIR="LibraxisAI/Llama-3.1-Nemotron-Ultra-253B-v1-MLX-Q8"
DEFAULT_QUANTIZE="y"
DEFAULT_BITS="8"
DEFAULT_GROUP_SIZE="64"
DEFAULT_DTYPE="float16"

# Get HF Path
echo -e "${BOLD}Hugging Face model path or local directory:${RESET}"
echo -e "(Default: ${DEFAULT_HF_PATH})"
read -p "> " HF_PATH
HF_PATH=${HF_PATH:-$DEFAULT_HF_PATH}

# Get output directory
echo -e "\n${BOLD}Output MLX model directory:${RESET}"
echo -e "(Default: ${DEFAULT_OUTPUT_DIR})"
read -p "> " MLX_PATH
MLX_PATH=${MLX_PATH:-$DEFAULT_OUTPUT_DIR}

# Ask about data type
echo -e "\n${BOLD}Model data type:${RESET}"
echo -e "(Default: ${DEFAULT_DTYPE}, Options: float16, bfloat16, float32)"
read -p "> " DTYPE
DTYPE=${DTYPE:-$DEFAULT_DTYPE}

# Ask about quantization
echo -e "\n${BOLD}Quantize the model? [y/n]${RESET}"
echo -e "(Default: ${DEFAULT_QUANTIZE})"
read -p "> " QUANTIZE
QUANTIZE=${QUANTIZE:-$DEFAULT_QUANTIZE}

# If quantizing, get more details
if [[ "$QUANTIZE" == "y" || "$QUANTIZE" == "Y" ]]; then
  echo -e "\n${BOLD}Quantization bits:${RESET}"
  echo -e "(Default: ${DEFAULT_BITS}, Options: 2, 3, 4, 6, 8)"
  read -p "> " BITS
  BITS=${BITS:-$DEFAULT_BITS}
  
  echo -e "\n${BOLD}Group size:${RESET}"
  echo -e "(Default: ${DEFAULT_GROUP_SIZE})"
  read -p "> " GROUP_SIZE
  GROUP_SIZE=${GROUP_SIZE:-$DEFAULT_GROUP_SIZE}

  echo -e "\n${BOLD}Quantization predicate:${RESET}"
  echo -e "(Default: none, Options: mixed_2_6, mixed_3_6, mixed_4_6)"
  echo -e "Leave empty for uniform quantization"
  read -p "> " QUANT_PREDICATE
  
  QUANT_OPTIONS="-q --q-bits ${BITS} --q-group-size ${GROUP_SIZE}"
  
  if [[ -n "$QUANT_PREDICATE" ]]; then
    QUANT_OPTIONS="${QUANT_OPTIONS} --quant-predicate ${QUANT_PREDICATE}"
  fi
else
  QUANT_OPTIONS=""
fi

# Ask about upload repository (optional)
echo -e "\n${BOLD}Upload repository (optional):${RESET}"
echo -e "(Leave empty to skip upload)"
read -p "> " UPLOAD_REPO

if [[ -n "$UPLOAD_REPO" ]]; then
  UPLOAD_OPTION="--upload-repo ${UPLOAD_REPO}"
else
  UPLOAD_OPTION=""
fi

# Build the command
CONVERT_CMD="mlx_lm.convert --hf-path ${HF_PATH} --mlx-path ${MLX_PATH} --dtype ${DTYPE} ${QUANT_OPTIONS} ${UPLOAD_OPTION}"

# Print the preview
echo -e "\n${BOLD}${YELLOW}Command Preview:${RESET}"
echo -e "$CONVERT_CMD"

# Expected outcomes based on options
echo -e "\n${BOLD}${YELLOW}Expected outcomes:${RESET}"
if [[ "$QUANTIZE" == "y" || "$QUANTIZE" == "Y" ]]; then
  if [[ "$BITS" == "8" ]]; then
    echo -e "- ${GREEN}Original model size: ~500GB (${DTYPE} format)${RESET}"
    echo -e "- ${GREEN}Expected result size: ~125GB (8-bit quantized)${RESET}"
    echo -e "- ${GREEN}Expected memory usage: 300-400GB peak${RESET}"
  elif [[ "$BITS" == "4" ]]; then
    echo -e "- ${GREEN}Original model size: ~500GB (${DTYPE} format)${RESET}"
    echo -e "- ${GREEN}Expected result size: ~62GB (4-bit quantized)${RESET}"
    echo -e "- ${GREEN}Expected memory usage: 200-300GB peak${RESET}"
  elif [[ -n "$QUANT_PREDICATE" ]]; then
    echo -e "- ${GREEN}Original model size: ~500GB (${DTYPE} format)${RESET}"
    echo -e "- ${GREEN}Using mixed precision quantization: ${QUANT_PREDICATE}${RESET}"
    echo -e "- ${GREEN}Variable memory requirements based on strategy${RESET}"
  else
    echo -e "- ${GREEN}Original model size: ~500GB (${DTYPE} format)${RESET}"
    echo -e "- ${GREEN}Custom quantization with ${BITS} bits${RESET}"
  fi
else
  echo -e "- ${GREEN}No quantization selected - model will remain in ${DTYPE} format${RESET}"
  echo -e "- ${GREEN}High memory requirements (400-500GB)${RESET}"
fi

echo -e "- ${GREEN}Expected conversion time: Several hours${RESET}"

# Command to run using python -m syntax
PYTHON_CMD="python -m mlx_lm.convert --hf-path ${HF_PATH} --mlx-path ${MLX_PATH} --dtype ${DTYPE} ${QUANT_OPTIONS} ${UPLOAD_OPTION}"

# Alternative format for running with uv
UV_CMD="uv run -m mlx_lm.convert --hf-path ${HF_PATH} --mlx-path ${MLX_PATH} --dtype ${DTYPE} ${QUANT_OPTIONS} ${UPLOAD_OPTION}"

# Ask for command format choice
echo -e "\n${BOLD}${GREEN}Choose command format:${RESET}"
echo -e "1. ${YELLOW}Direct command: ${RESET}${CONVERT_CMD}"
echo -e "2. ${YELLOW}Python module: ${RESET}${PYTHON_CMD}"
echo -e "3. ${YELLOW}Using UV: ${RESET}${UV_CMD}"
read -p "> " FORMAT_CHOICE

case "$FORMAT_CHOICE" in
  1)
    FINAL_CMD="${CONVERT_CMD}"
    ;;
  2)
    FINAL_CMD="${PYTHON_CMD}"
    ;;
  3)
    FINAL_CMD="${UV_CMD}"
    ;;
  *)
    FINAL_CMD="${CONVERT_CMD}"
    ;;
esac

# Give preparation tips
echo -e "\n${BOLD}${BLUE}Preparation tips:${RESET}"
echo -e "1. ${YELLOW}Ensure Mac is plugged in and won't sleep${RESET}"
echo -e "2. ${YELLOW}Close other memory-intensive applications${RESET}"
echo -e "3. ${YELLOW}Be prepared for high fan speeds and heat${RESET}"
echo -e "4. ${YELLOW}The process may appear to hang at times - this is normal${RESET}"

# Print the final command
echo -e "\n${BOLD}${RED}Your conversion command:${RESET}"
echo -e "${FINAL_CMD}"

# Copy to clipboard option
echo -e "\n${BOLD}${GREEN}Copy command to clipboard? [y/n]${RESET}"
read -p "> " COPY_CMD

if [[ "$COPY_CMD" == "y" || "$COPY_CMD" == "Y" ]]; then
    echo "${FINAL_CMD}" | pbcopy
    echo -e "${GREEN}Command copied to clipboard!${RESET}"
fi

# Test command template
TEST_CMD="mlx_lm.generate --model ${MLX_PATH} --prompt \"Explain quantum computing in simple terms.\" --max-tokens 100"

echo -e "\n${BOLD}${BLUE}After conversion, test with:${RESET}"
echo -e "${TEST_CMD}"

# Memory check command
MEM_CMD="python -c \"import mlx.core as mx; print(f'Peak memory: {mx.metal.get_peak_memory()/1e9:.2f} GB')\""

echo -e "\n${BOLD}${BLUE}To check memory usage:${RESET}"
echo -e "${MEM_CMD}"

echo -e "\n${BOLD}${BLUE}=====================================${RESET}"
echo -e "${BOLD}${GREEN}Command generator complete!${RESET}"
echo -e "${BOLD}${BLUE}=====================================${RESET}"