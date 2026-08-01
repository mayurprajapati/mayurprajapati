import asyncio
import os
from playwright.async_api import async_playwright


async def convert_html_to_dynamic_single_page_pdf(
    html_file_path: str, output_pdf_path: str, width_px: int = 1200
):
    abs_path = os.path.abspath(html_file_path)
    file_uri = f"file://{abs_path}"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.set_viewport_size({"width": width_px, "height": 800})
        await page.goto(file_uri, wait_until="networkidle")

        # 1. Force screen media type so CSS @media print rules don't break layout
        await page.emulate_media(media="screen")

        # 2. Get exact dimensions
        dimensions = await page.evaluate("""() => {
            const body = document.body;
            const html = document.documentElement;
            return {
                height: Math.max(body.scrollHeight, body.offsetHeight, html.scrollHeight, html.offsetHeight),
                width: Math.max(body.scrollWidth, body.offsetWidth, html.scrollWidth, html.offsetWidth)
            };
        }""")

        content_height = dimensions["height"]
        content_width = dimensions["width"]

        # 3. Inject CSS @page override directly into HTML DOM
        await page.add_style_tag(
            content=f"""
            @page {{
                size: {content_width}px {content_height}px !important;
                margin: 0 !important;
            }}
            html, body {{
                margin: 0 !important;
                padding: 0 !important;
                height: {content_height}px !important;
                overflow: hidden !important;
            }}
            * {{
                break-inside: avoid !important;
                page-break-inside: avoid !important;
            }}
        """
        )

        # 4. Generate PDF
        await page.pdf(
            path=output_pdf_path,
            width=f"{content_width}px",
            height=f"{content_height}px",
            print_background=True,
            prefer_css_page_size=True,  # Mandatory when using dynamic @page size
            margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"},
        )

        await browser.close()
        print(f"Generated PDF ({content_width}px x {content_height}px) -> {output_pdf_path}")


if __name__ == "__main__":
    asyncio.run(
        convert_html_to_dynamic_single_page_pdf(
            html_file_path="resume/index.html",
            output_pdf_path="resume/Mayur_Prajapati_Resume.pdf",
        )
    )