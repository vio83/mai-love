#!/usr/bin/env python3
"""Wrapper per forzare integrazione video 3D su webui.py attuale."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import webui as base  # noqa: E402

# Estensioni asset video
if hasattr(base, "ALLOWED_EXT"):
    base.ALLOWED_EXT.update({".mp4", ".webm", ".mov", ".m4v"})
if hasattr(base, "ALLOWED_EXTENSIONS"):
    base.ALLOWED_EXTENSIONS.update({".mp4", ".webm", ".mov", ".m4v"})

html = base.HTML_PAGE

html = html.replace(
    "img-src 'self';\">",
    "img-src 'self'; media-src 'self';\">",
)

html = html.replace(
    '<img id="bg-photo" src="/assets/lobby_chandelier.jpg" alt="">\n<canvas id="canvas-overlay"></canvas>',
    '<div id="bg-scene">\n'
    '  <img id="bg-photo" src="/assets/lobby_chandelier.jpg" alt="">\n'
    '  <video id="bg-video" autoplay muted loop playsinline preload="metadata">\n'
    '    <source id="bg-video-source" src="/assets/design_3d.m4v" type="video/mp4">\n'
    '  </video>\n'
    '</div>\n'
    '<canvas id="canvas-overlay"></canvas>',
)

html = html.replace(
    '#bg-photo{position:fixed;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;filter:brightness(0.55) saturate(1.1)}',
    '#bg-scene{position:fixed;inset:0;z-index:0;overflow:hidden;transform-style:preserve-3d;perspective:1200px}\n'
    '#bg-photo,#bg-video{position:absolute;inset:-3%;width:106%;height:106%;object-fit:cover;transition:transform .2s linear,opacity .6s ease;will-change:transform,opacity}\n'
    '#bg-photo{z-index:0;filter:brightness(0.55) saturate(1.1)}\n'
    '#bg-video{z-index:1;opacity:0;filter:brightness(0.58) saturate(1.15) contrast(1.05)}\n'
    'body.video-ready #bg-video{opacity:.72}\n'
    'body.video-ready #bg-photo{opacity:.38}',
)

if '.media-chip{' not in html:
    html = html.replace(
        '.photo-thumb img{width:100%;height:100%;object-fit:cover}',
        '.photo-thumb img{width:100%;height:100%;object-fit:cover}\n'
        '.media-chip{width:auto;min-width:62px;padding:0 10px;height:48px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:700;letter-spacing:.7px;color:#f5dfa0;background:rgba(10,10,15,0.72);border:2px solid rgba(201,168,76,0.25);cursor:pointer;opacity:.7;transition:all .2s}\n'
        '.media-chip.active{opacity:1;border-color:#c9a84c;box-shadow:0 0 14px rgba(201,168,76,0.25)}',
    )

html = html.replace(
    '<div id="photo-switcher">\n  <div class="photo-thumb active" onclick="switchPhoto(\'lobby_chandelier.jpg\',this)"><img src="/assets/lobby_chandelier.jpg" alt=""></div>',
    '<div id="photo-switcher">\n'
    '  <div class="media-chip active" onclick="switchVideo(\'design_3d.m4v\',this)">VIDEO 3D</div>\n'
    '  <div class="photo-thumb" onclick="switchPhoto(\'lobby_chandelier.jpg\',this)"><img src="/assets/lobby_chandelier.jpg" alt=""></div>',
)

old_switch = "function switchPhoto(f,el){document.getElementById('bg-photo').src='/assets/'+f;var ts=document.querySelectorAll('.photo-thumb');for(var i=0;i<ts.length;i++)ts[i].classList.remove('active');el.classList.add('active')}"
new_switch = (
    "var bgPhoto=document.getElementById('bg-photo');\n"
    "var bgVideo=document.getElementById('bg-video');\n"
    "var bgVideoSource=document.getElementById('bg-video-source');\n"
    "if(bgVideo){\n"
    "  bgVideo.addEventListener('canplay',function(){\n"
    "    document.body.classList.add('video-ready');\n"
    "  });\n"
    "  bgVideo.addEventListener('error',function(){\n"
    "    document.body.classList.remove('video-ready');\n"
    "  });\n"
    "}\n"
    "function setActiveMedia(el){\n"
    "  var ts=document.querySelectorAll('.photo-thumb,.media-chip');\n"
    "  for(var i=0;i<ts.length;i++)ts[i].classList.remove('active');\n"
    "  if(el)el.classList.add('active');\n"
    "}\n"
    "function switchPhoto(f,el){\n"
    "  if(bgPhoto)bgPhoto.src='/assets/'+f;\n"
    "  document.body.classList.remove('video-ready');\n"
    "  if(bgVideo){\n"
    "    try{bgVideo.pause()}catch(_e){}\n"
    "  }\n"
    "  setActiveMedia(el);\n"
    "}\n"
    "function switchVideo(f,el){\n"
    "  if(bgVideoSource){\n"
    "    bgVideoSource.src='/assets/'+f;\n"
    "  }\n"
    "  if(bgVideo){\n"
    "    bgVideo.load();\n"
    "    var p=bgVideo.play();\n"
    "    if(p&&p.catch){\n"
    "      p.catch(function(){\n"
    "        document.body.classList.remove('video-ready');\n"
    "      });\n"
    "    }\n"
    "  }\n"
    "  setActiveMedia(el);\n"
    "}"
)
html = html.replace(old_switch, new_switch)

html = html.replace(
    'mime = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".gif":"image/gif",".webp":"image/webp",".svg":"image/svg+xml",".ico":"image/x-icon"}',
    'mime = {".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".gif":"image/gif",".webp":"image/webp",".svg":"image/svg+xml",".ico":"image/x-icon",".mp4":"video/mp4",".webm":"video/webm",".mov":"video/quicktime",".m4v":"video/mp4"}',
)

base.HTML_PAGE = html

if __name__ == "__main__":
    print("[BRACE] Wrapper video attivo -> design_3d.m4v")
    base.main()
