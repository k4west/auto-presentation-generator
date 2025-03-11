import subprocess

class MarpRenderer:
    """MARP 기반 프레젠테이션 변환기"""

    @staticmethod
    def render(md_file: str, output_format: str) -> str:
        if output_format not in ["pdf", "pptx"]:
            raise ValueError("지원되지 않는 형식입니다. (pdf 또는 pptx 선택)")

        output_file = md_file.replace(".md", f".{output_format}")
        subprocess.run(["marp", md_file, f"--{output_format}", "-o", output_file], check=True)
        return output_file
