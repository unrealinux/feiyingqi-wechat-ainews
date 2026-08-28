# baoyu-cover-image Preferences (Project)

## Image Backend
# Pin to the baoyu-image-gen skill (dashscope backend used by cover_generator.py).
preferred_image_backend: baoyu-image-gen

## Defaults
default_aspect: "16:9"     # WeChat article covers use 16:9
language: zh              # Chinese titles
preferred_type: null      # auto-select
preferred_palette: elegant
quick_mode: false         # keep confirmation per policy

## Watermark
watermark:
  enabled: false
  content: "AI前沿观察"
  position: bottom-right
