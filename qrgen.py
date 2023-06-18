import torch
import gradio as gr
import qrcode
from pathlib import Path
from PIL import Image
from diffusers import (StableDiffusionPipeline, StableDiffusionControlNetImg2ImgPipeline, ControlNetModel,
                       DDIMScheduler, DPMSolverMultistepScheduler, DEISMultistepScheduler, 
                       HeunDiscreteScheduler, EulerDiscreteScheduler,)


def inference( qr_code_content: str, prompt: str, negative_prompt: str, guidance_scale: float = 10.0,
               controlnet_conditioning_scale: float = 2.0, strength: float = 0.8, seed: int = -1,
               init_image: Image.Image | None = None, qrcode_image: Image.Image | None = None, 
               use_qr_code_as_init_image = True, sampler = "DPM++ Karras SDE",):
    if prompt is None or prompt == "": raise gr.Error("Prompt is required")
    if qrcode_image is None and qr_code_content == "": raise gr.Error("QR Code Image or QR Code Content is required")
    pipe.scheduler = SAMPLER_MAP[sampler](pipe.scheduler.config)
    generator = torch.manual_seed(seed) if seed != -1 else torch.Generator()
    if qr_code_content != "" or qrcode_image.size == (1, 1):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4,)
        qr.add_data(qr_code_content)
        qr.make(fit=True)
        qrcode_image = qr.make_image(fill_color="black", back_color="white")
        qrcode_image = resize_for_condition_image(qrcode_image, 768)
    else: qrcode_image = resize_for_condition_image(qrcode_image, 768)
    init_image = qrcode_image
    out = pipe(prompt=prompt, negative_prompt=negative_prompt, image=qrcode_image, control_image=qrcode_image, width=768,
               height=768, guidance_scale=float(guidance_scale),
               controlnet_conditioning_scale=float(controlnet_conditioning_scale), generator=generator, 
               strength=float(strength), num_inference_steps=40,)
    return out.images[0]
    torch.cuda.empty_cache()


def resize_for_condition_image(input_image: Image.Image, resolution: int):
    input_image = input_image.convert("RGB")
    W, H = input_image.size
    k = float(resolution) / min(H, W)
    H *= k
    W *= k
    H = int(round(H / 64.0)) * 64
    W = int(round(W / 64.0)) * 64
    img = input_image.resize((W, H), resample=Image.LANCZOS)
    return img


SAMPLER_MAP = {
    "DPM++ Karras SDE": lambda config: DPMSolverMultistepScheduler.from_config(config, use_karras=True, algorithm_type="sde-dpmsolver++"),
    "DPM++ Karras": lambda config: DPMSolverMultistepScheduler.from_config(config, use_karras=True),
    "Euler": lambda config: EulerDiscreteScheduler.from_config(config),
    "DEIS": lambda config: DEISMultistepScheduler.from_config(config),}
qrcode_generator = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_H, box_size=10, border=4,)
controlnet = ControlNetModel.from_pretrained("DionTimmer/controlnet_qrcode-control_v1p_sd15", torch_dtype=torch.float16)
pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained("SG161222/Realistic_Vision_V2.0",controlnet=controlnet,
                                                                safety_checker=None,torch_dtype=torch.float16,)
torch.cuda.empty_cache()
pipe.to("cuda")
pipe.enable_vae_tiling()
pipe.enable_attention_slicing("max")
pipe.enable_xformers_memory_efficient_attention(attention_op=None)
pipe.unet.to(memory_format=torch.channels_last)
pipe.enable_sequential_cpu_offload()
torch.cuda.empty_cache()

with gr.Blocks() as blocks:
    with gr.Row():
        with gr.Column():
            qr_code_content = gr.Textbox(label="QR Code Content or URL", value="",)
            with gr.Accordion(label="QR Code Image (Optional)", open=False):
                qr_code_image = gr.Image(label="QR Code Image (Optional). Leave blank to automatically generate QR code",
                                         type="pil",)
            prompt = gr.Textbox(label="Prompt", value="")
            negative_prompt = gr.Textbox(label="Negative Prompt", value="ugly, tiling, out of frame, watermark, signature, cut off, low contrast, underexposed, overexposed, beginner, amateur, bad texture, bad reflections",)
            seed = gr.Slider(minimum=-1, maximum=9999999999, step=1, value=2313123, label="Seed", randomize=True,)
            with gr.Accordion(label="Init Images (Optional)", open=False, visible=False) as init_image_acc:
                init_image = gr.Image(label="Init Image (Optional)", type="pil")
            with gr.Accordion(label="Params:", open=False,):
                use_qr_code_as_init_image = gr.Checkbox(label="Use QR code as init image", value=True, interactive=False,
                                                        info="Whether init image should be QR code. Unclick to pass init image")
                controlnet_conditioning_scale = gr.Slider(minimum=0.0, maximum=5.0, step=0.01, value=1.1,
                                                          label="Controlnet Conditioning Scale",)
                strength = gr.Slider(minimum=0.0, maximum=1.0, step=0.01, value=0.9, label="Strength")
                guidance_scale = gr.Slider(minimum=0.0, maximum=50.0, step=0.25, value=7.5, label="Guidance Scale",)
                sampler = gr.Dropdown(label="Sampler", choices=list(SAMPLER_MAP.keys()), value="DPM++ Karras SDE")
                gr.Label("Ex Prompt: award winning photography of balanced stones in water, minimalism, long time exposure, desaturated, 80mm lens, realistic photo, sharp stone texture, good reflections")
            with gr.Row(): run_btn = gr.Button("Run")
        with gr.Column(): result_image = gr.Image(label="Result Image")
    run_btn.click(inference,inputs=[qr_code_content, prompt, negative_prompt, guidance_scale, 
                                    controlnet_conditioning_scale, strength, seed, init_image, qr_code_image,
                                    use_qr_code_as_init_image, sampler,], outputs=[result_image],)
print("\n\n")
blocks.queue(concurrency_count=1, max_size=20)
blocks.launch(share=False)
