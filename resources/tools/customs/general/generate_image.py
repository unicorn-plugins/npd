"""
Nano Banana (Gemini) 이미지 생성 스크립트
"""
import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini Nano Banana model",
        epilog="""
Examples:
  python generate_image.py --prompt "아침 바다를 걷는 여성"
  python generate_image.py --prompt-file prompt.txt --output-dir ./images
  python generate_image.py --prompt "sunset beach" --output-dir ./results --output-name beach_sunset
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Mutually exclusive group for prompt input
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument(
        "--prompt",
        type=str,
        help="Prompt text for image generation"
    )
    prompt_group.add_argument(
        "--prompt-file",
        type=str,
        help="Path to file containing the prompt text"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory where the generated image is saved (default: current directory)"
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default="generated_image",
        help="Output filename without extension (default: generated_image)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Gemini API key (overrides .env file)"
    )

    args = parser.parse_args()

    # Load API key
    if args.api_key:
        api_key = args.api_key
    else:
        env_path = os.path.join('.', 'tools', '.env')
        load_dotenv(env_path)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            parser.error("GEMINI_API_KEY not found in .env file. Use --api-key to provide it.")

    # Get prompt
    if args.prompt:
        prompt = args.prompt
    else:
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()

    # Create output directory if needed
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate image
    client = genai.Client(api_key=api_key)

    system_prompt = "Always use a clean white background (#FFFFFF) for all generated images. 모든 텍스트는 한글로 작성하고, 꼭 필요한 경우에만 영문을 사용하세요 (예: SKILL.md, Haiku, Sonnet, Opus 등 고유명사)."

    response = client.models.generate_content(
        model="nano-banana-pro-preview",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            system_instruction=system_prompt,
        ),
    )

    # Save results
    output_path = output_dir / f"{args.output_name}.png"

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.inline_data
            with open(output_path, "wb") as f:
                f.write(image.data)
            print(f"Image saved: {output_path} ({len(image.data)} bytes)")


if __name__ == "__main__":
    main()
