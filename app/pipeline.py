"""Processing pipeline for content generation."""

from __future__ import annotations

import asyncio
import os
from typing import Optional

from .models import Job
from . import openrouter, gemini

SYSTEM_PROMPT = "Anda asisten penulis konten YouTube faceless. Hasil orisinal. Gunakan bahasa {language}. Kalimat pendek. Suara aktif. Hindari frasa identik. Tambahkan konteks unik saat relevan. Hindari klaim berisiko tanpa penjelasan sederhana."

TASK_TEMPLATES = {
    "summary": (
        "Buat 10 sampai 15 bullet poin informatif dalam {language} untuk niche {niche}. "
        "Gaya {persona}. Jangan salin frasa sumber. Transkrip berikut:\n{transcript}"
    ),
    "reframe": (
        "Kembangkan sudut pandang baru dan insight tambahan dari poin ringkasan. "
        "Originality level {originality_level}. Hasilkan versi ringkas 300 sampai 500 kata. Bahasa {language}."
    ),
    "outline": (
        "Susun outline video faceless durasi target {target_duration_min} menit. 8 sampai 12 bab. "
        "Tiap bab punya tujuan jelas. Perkirakan durasi tiap bab 45 sampai 90 detik. Bahasa {language}."
    ),
    "script": (
        "Tulis skrip narasi lengkap sesuai outline. Hook 15 detik pertama kuat. "
        "Kalimat pendek. Aktif. Hindari repetisi. Sisipkan CTA di penutup. Sesuaikan nada {persona}. Bahasa {language}. "
        "Panjang mendekati {target_duration_min} menit saat dibacakan cepat."
    ),
    "titles": (
        "Buat 10 judul CTR tinggi. 55 sampai 65 karakter. Hindari clickbait berlebihan. Sertakan manfaat jelas. Bahasa {language}."
    ),
    "desc_tags": (
        "Tulis deskripsi 2 paragraf SEO friendly. Paragraf 1 manfaat utama. Paragraf 2 ajakan tindak lanjut. "
        "Tambahkan 10 sampai 15 keyword tag pendek. Bahasa {language}."
    ),
}


async def run_task(model: str, system_prompt: str, user_prompt: str, use_gemini: bool = False) -> str:
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    if not use_gemini:
        return await openrouter.chat_completion(model, messages)
    return await gemini.generate(model, system_prompt, user_prompt)


async def process_job(job: Job, transcript: str, model: str, fallback_model: str = "gemini-pro") -> Job:
    """Run full pipeline updating job outputs."""
    job.status = "running"
    system_prompt = SYSTEM_PROMPT.format(language=job.language)
    try:
        summary_prompt = TASK_TEMPLATES["summary"].format(
            language=job.language,
            niche=job.niche,
            persona=job.persona,
            transcript=transcript,
        )
        summary = await run_task(model, system_prompt, summary_prompt)
        job.outputs.summary_points = [s.strip("- ") for s in summary.splitlines() if s.strip()]

        reframe_prompt = TASK_TEMPLATES["reframe"].format(
            language=job.language,
            originality_level=job.originality_level,
        )
        reframe = await run_task(model, system_prompt, reframe_prompt)
        # Not stored separately; used to enrich outline

        outline_prompt = TASK_TEMPLATES["outline"].format(
            language=job.language,
            target_duration_min=job.target_duration_min,
        )
        outline = await run_task(model, system_prompt, outline_prompt)
        job.outputs.outline = [o.strip("- ") for o in outline.splitlines() if o.strip()]

        script_prompt = TASK_TEMPLATES["script"].format(
            language=job.language,
            persona=job.persona,
            target_duration_min=job.target_duration_min,
        )
        job.outputs.script_text = await run_task(model, system_prompt, script_prompt)

        titles_prompt = TASK_TEMPLATES["titles"].format(language=job.language)
        titles = await run_task(model, system_prompt, titles_prompt)
        job.outputs.titles = [t.strip("- ") for t in titles.splitlines() if t.strip()]

        desc_tags_prompt = TASK_TEMPLATES["desc_tags"].format(language=job.language)
        desc_tags = await run_task(model, system_prompt, desc_tags_prompt)
        parts = desc_tags.split("Tags:")
        job.outputs.description = parts[0].strip()
        if len(parts) > 1:
            job.outputs.keywords = [k.strip().strip("#") for k in parts[1].split(',') if k.strip()]

        job.status = "done"
    except Exception:
        # Fallback to Gemini once
        if model != fallback_model:
            return await process_job(job, transcript, fallback_model, fallback_model)
        job.status = "error"
        raise
    return job
