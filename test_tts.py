"""TTS 全链路测试"""
import asyncio
import os, uuid, sys

async def main():
    print("=== TTS 链路测试 ===")
    
    # 1. TTS
    import edge_tts
    voice = "zh-CN-YunxiNeural"
    text = "鲲鹏志辩论系统测试，语音生成链路正常。"
    fid = f"tts/test_{uuid.uuid4().hex[:8]}.mp3"
    tmp = f"/tmp/{uuid.uuid4().hex}.mp3"
    
    print(f"[1/3] TTS 生成: {text[:20]}...")
    await edge_tts.Communicate(text, voice).save(tmp)
    size = os.path.getsize(tmp)
    print(f"  OK: {size} bytes -> {tmp}")
    
    # 2. R2 upload
    import httpx
    ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]
    BUCKET = os.environ["R2_BUCKET"]
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/r2/buckets/{BUCKET}/objects/{fid}"
    with open(tmp, "rb") as f:
        data = f.read()
    
    print(f"[2/3] R2 上传: {fid}")
    r = httpx.put(url, headers={"Authorization": f"Bearer {TOKEN}"}, content=data, timeout=30)
    if r.status_code == 200 and r.json().get("success"):
        print(f"  OK: 上传成功")
    else:
        print(f"  FAIL: {r.status_code} {r.text[:200]}")
        return
    os.remove(tmp)
    
    # 3. Public access
    pub_base = os.environ.get("R2_PUBLIC_BASE", "https://pub-777cf729d9534822b99f4ab446ac6059.r2.dev")
    pub_url = f"{pub_base}/{fid}"
    print(f"[3/3] 公网: {pub_url}")
    r2 = httpx.get(pub_url, timeout=30)
    if r2.status_code == 200:
        print(f"  OK: {len(r2.content)} bytes 可播放")
    else:
        print(f"  FAIL: {r2.status_code}")
    
    print("\n=== 测试完毕 ===")

asyncio.run(main())
