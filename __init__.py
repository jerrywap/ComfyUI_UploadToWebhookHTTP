import os
import json
import numpy as np
import requests
from PIL import Image

import folder_paths
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

class UploadToWebHookHTTP:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "webhook_url": ("STRING", {"default": "https://example.com/path_to_webhook"}),
                "frame_rate": ("INT", {"default": 12, "min": 1, "max": 60, "step": 1}),
                "save_image": ("BOOLEAN", {"default": True}),
                "prompt_id": ("STRING", {"default": ""}),
                "other_data": (
                    "STRING",
                    {
                        "default": "{\n  \"key1\": \"value1\",\n  \"key2\": \"value2\"\n}",
                        "multiline": True
                    }
                )
            },
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    CATEGORY = "JerrywapWebhookHTTP"
    FUNCTION = "generate_and_upload_video"

    def generate_and_upload_video(
        self,
        images,
        webhook_url: str,
        frame_rate: int,
        save_image=True,
        prompt_id: str = "",
        other_data: str = "{}"
    ):
        output_dir = folder_paths.get_output_directory() if save_image else folder_paths.get_temp_directory()

        (
            full_output_folder,
            filename,
            counter,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path("final", output_dir)

        # Prepare payload
        try:
            parsed_data = json.loads(other_data)
        except json.JSONDecodeError:
            parsed_data = {}

        if prompt_id:
            parsed_data["prompt_id"] = prompt_id

        if len(images) == 1:
            single_file_path = os.path.join(full_output_folder, f"{filename}_.png")
            single_image = 255.0 * images[0].cpu().numpy()
            single_image_pil = Image.fromarray(single_image.astype(np.uint8))
            single_image_pil.save(single_file_path)

            with open(single_file_path, "rb") as file:
                response = requests.post(
                    webhook_url,
                    files={"file": ("image.png", file, "image/png")},
                    data=parsed_data
                )

        else:
            frames = [255.0 * image.cpu().numpy() for image in images]
            clip = ImageSequenceClip(frames, fps=frame_rate)
            file_path = os.path.join(full_output_folder, f"{filename}_{counter:05}_.mp4")
            clip.write_videofile(file_path, codec="libx264", fps=frame_rate)

            with open(file_path, "rb") as file_data:
                response = requests.post(
                    webhook_url,
                    files={"file": ("video.mp4", file_data, "video/mp4")},
                    data=parsed_data
                )

        # Response output
        if response.status_code == 200 or response.status_code == 201 or response.status_code == 204:
            print("✅ Successfully uploaded to Webhook.")
            print(f"Response Code: {response.status_code}")
            print(f"Response Text: {response.text}")
        else:
            print(f"❌ Failed to upload. Status code: {response.status_code} - {response.text}")

        return ("Uploading Completed",)


NODE_CLASS_MAPPINGS = {
    "UploadToWebHookHTTP": UploadToWebHookHTTP,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UploadToWebHookHTTP": "Send To Http Webhook",
}
