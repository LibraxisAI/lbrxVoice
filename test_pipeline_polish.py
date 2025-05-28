#!/usr/bin/env python3
"""
Test full pipeline with Polish conversation
"""

import requests
import json
import base64
import time
import os
from pathlib import Path
import soundfile as sf
import numpy as np

class PolishPipelineTest:
    def __init__(self):
        self.base_dir = Path("test_pipeline")
        self.conversations = [
            {
                "id": "rozmowa_1",
                "text": "[S1] Cześć! Jak się masz? [S2] Dziękuję, świetnie! A ty? [S1] Też dobrze, właśnie testuję nowy system rozpoznawania mowy.",
                "description": "Podstawowa rozmowa"
            },
            {
                "id": "rozmowa_2", 
                "text": "[S1] Czy wiesz, że ten model potrafi generować śmiech? (laughs) [S2] Naprawdę? To niesamowite! (laughs) [S1] Tak, i może też symulować westchnienia. (sighs)",
                "description": "Rozmowa z elementami niewerbalnymi"
            },
            {
                "id": "rozmowa_3",
                "text": "[S1] Opowiedz mi o pogodzie w Krakowie. [S2] Dzisiaj w Krakowie jest piękna słoneczna pogoda, temperatura około dwudziestu stopni. [S1] Świetnie, może pójdziemy na spacer?",
                "description": "Rozmowa o pogodzie"
            }
        ]
        
    def test_servers_health(self):
        """Check if all servers are running"""
        print("\n🏥 Sprawdzam serwery...")
        
        servers = {
            "Whisper Batch": "http://localhost:8123/health",
            "Whisper Realtime": "http://localhost:8000/health", 
            "DIA REST": "http://localhost:8125/health",
            "CSM REST": "http://localhost:8126/health"
        }
        
        all_ok = True
        for name, url in servers.items():
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    print(f"✅ {name}: Działa")
                else:
                    print(f"❌ {name}: Problem (status {resp.status_code})")
                    all_ok = False
            except:
                print(f"❌ {name}: Nie odpowiada")
                all_ok = False
                
        return all_ok
        
    def generate_tts_dia(self, text, output_file):
        """Generate speech using DIA"""
        print(f"\n🎤 Generuję mowę (DIA): {text[:50]}...")
        
        try:
            response = requests.post(
                "http://localhost:8125/synthesize_sync",
                json={
                    "text": text,
                    "temperature": 0.8,
                    "top_p": 0.95
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                audio_base64 = data["audio_data"]
                
                # Decode and save
                audio_bytes = base64.b64decode(audio_base64)
                output_path = self.base_dir / "tts_outputs" / output_file
                
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                    
                print(f"✅ Zapisano: {output_path}")
                return str(output_path)
            else:
                print(f"❌ Błąd DIA: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return None
            
    def generate_tts_csm(self, text, output_file, speaker_id=0):
        """Generate speech using CSM"""
        print(f"\n🎤 Generuję mowę (CSM, speaker {speaker_id}): {text[:50]}...")
        
        try:
            response = requests.post(
                "http://localhost:8126/synthesize_sync",
                json={
                    "text": text,
                    "speaker_id": str(speaker_id),
                    "temperature": 0.8
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                audio_base64 = data["audio_data"]
                
                # Decode and save
                audio_bytes = base64.b64decode(audio_base64)
                output_path = self.base_dir / "tts_outputs" / output_file
                
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
                    
                print(f"✅ Zapisano: {output_path}")
                return str(output_path)
            else:
                print(f"❌ Błąd CSM: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return None
            
    def transcribe_whisper(self, audio_path):
        """Transcribe audio using Whisper"""
        print(f"\n📝 Transkrybuję: {audio_path}")
        
        try:
            with open(audio_path, "rb") as f:
                files = {"file": (Path(audio_path).name, f, "audio/wav")}
                data = {"language": "pl"}  # Polish language
                
                response = requests.post(
                    "http://localhost:8123/transcribe",
                    files=files,
                    data=data
                )
                
            if response.status_code in [200, 202]:
                result = response.json()
                
                if "transcription" in result:
                    print(f"✅ Transkrypcja: {result['transcription']}")
                    return result['transcription']
                elif "job_id" in result:
                    # Poll for result
                    job_id = result["job_id"]
                    print(f"⏳ Czekam na transkrypcję (job {job_id})...")
                    
                    for _ in range(30):  # Max 30 seconds
                        time.sleep(1)
                        status_resp = requests.get(
                            f"http://localhost:8123/status/{job_id}"
                        )
                        status = status_resp.json()
                        
                        if status["status"] == "completed":
                            print(f"✅ Transkrypcja: {status['transcription']}")
                            return status['transcription']
                        elif status["status"] == "failed":
                            print(f"❌ Błąd: {status.get('error')}")
                            return None
                            
            else:
                print(f"❌ Błąd Whisper: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return None
            
    def run_full_test(self):
        """Run complete pipeline test"""
        print("\n🚀 Test pełnego pipeline'u - Polska rozmowa")
        print("=" * 60)
        
        # Check servers
        if not self.test_servers_health():
            print("\n⚠️  Niektóre serwery nie działają!")
            print("Uruchom je najpierw:")
            print("  whisper-batch-server")
            print("  python -m tts_servers dia-rest") 
            print("  python -m tts_servers csm-rest")
            return
            
        results = []
        
        # Test 1: DIA conversations
        print("\n\n📍 TEST 1: Rozmowy przez DIA")
        print("-" * 40)
        
        for conv in self.conversations:
            print(f"\n🎭 {conv['description']}")
            
            # Generate with DIA
            audio_file = self.generate_tts_dia(
                conv["text"], 
                f"dia_{conv['id']}.wav"
            )
            
            if audio_file:
                # Transcribe
                transcription = self.transcribe_whisper(audio_file)
                
                results.append({
                    "test": f"DIA - {conv['description']}",
                    "original": conv["text"],
                    "transcription": transcription,
                    "audio_file": audio_file
                })
                
                # Save comparison
                comp_file = self.base_dir / "conversations" / f"dia_{conv['id']}_comparison.txt"
                with open(comp_file, "w", encoding="utf-8") as f:
                    f.write(f"=== {conv['description']} ===\n\n")
                    f.write(f"ORYGINAŁ:\n{conv['text']}\n\n")
                    f.write(f"TRANSKRYPCJA:\n{transcription}\n\n")
                    
        # Test 2: CSM with different speakers
        print("\n\n📍 TEST 2: Ten sam tekst, różni mówcy CSM")
        print("-" * 40)
        
        test_text = "Cześć! To jest test systemu syntezy mowy. Czy słyszysz mnie wyraźnie?"
        
        for speaker_id in [0, 1, 2, 3]:
            print(f"\n🎤 CSM Speaker {speaker_id}")
            
            audio_file = self.generate_tts_csm(
                test_text,
                f"csm_speaker_{speaker_id}.wav",
                speaker_id
            )
            
            if audio_file:
                transcription = self.transcribe_whisper(audio_file)
                
                results.append({
                    "test": f"CSM Speaker {speaker_id}",
                    "original": test_text,
                    "transcription": transcription,
                    "audio_file": audio_file
                })
                
        # Summary
        print("\n\n📊 PODSUMOWANIE TESTÓW")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['test']}")
            print(f"   Oryginał:     {result['original'][:60]}...")
            if result['transcription']:
                print(f"   Transkrypcja: {result['transcription'][:60]}...")
                
                # Calculate simple accuracy (word match)
                orig_words = result['original'].lower().replace('[s1]', '').replace('[s2]', '').split()
                trans_words = result['transcription'].lower().split()
                common = set(orig_words) & set(trans_words)
                accuracy = len(common) / len(orig_words) * 100 if orig_words else 0
                print(f"   Dokładność:   ~{accuracy:.1f}% słów")
            else:
                print(f"   Transkrypcja: BŁĄD")
                
        # Save full results
        results_file = self.base_dir / "conversations" / "wyniki_testow.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"\n\n✅ Wyniki zapisane w: {results_file}")
        print(f"📁 Pliki audio: {self.base_dir}/tts_outputs/")
        print(f"📁 Porównania: {self.base_dir}/conversations/")


def main():
    tester = PolishPipelineTest()
    tester.run_full_test()


if __name__ == "__main__":
    main()