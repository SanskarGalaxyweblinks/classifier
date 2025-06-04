"""
Simple CSV Email Testing Script - Calls API endpoints
"""

import pandas as pd
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any

class SimpleCSVTester:
    def __init__(self, api_base_url: str = "http://0.0.0.0:8080/api"):
        """Initialize with API URL"""
        self.api_base_url = api_base_url
        self.classify_url = f"{api_base_url}/classify"
        self.reply_url = f"{api_base_url}/generate_reply"
        
        print(f"🔗 API Base URL: {api_base_url}")
        
        # Test API connection
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API connection successful")
            else:
                print(f"⚠️ API responded with status: {response.status_code}")
        except Exception as e:
            print(f"❌ API connection failed: {e}")

    def process_csv(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Process CSV file using API calls"""
        
        print(f"📁 Loading CSV file: {csv_file_path}")
        
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        print(f"📊 Loaded {len(df)} emails from CSV")
        
        results = []
        
        print("\n" + "="*60)
        print("🚀 STARTING EMAIL PROCESSING VIA API")
        print("="*60)
        
        for index, row in df.iterrows():
            email_id = index + 1
            subject = str(row['subject']) if pd.notna(row['subject']) else ""
            body = str(row['body']) if pd.notna(row['body']) else ""
            
            print(f"\n📧 Processing Email #{email_id}")
            print(f"📝 Subject: {subject[:50]}...")
            print(f"📄 Body Length: {len(body)} characters")
            
            # Step 1: Call Classification API
            print("🔍 Step 1: Calling classification API...")
            try:
                classify_payload = {
                    "subject": subject,
                    "body": body,
                    "has_attachments": False
                }
                
                start_time = time.time()
                response = requests.post(self.classify_url, json=classify_payload, timeout=30)
                classification_time = time.time() - start_time
                
                if response.status_code == 200:
                    classify_result = response.json()
                    classification_data = classify_result["results"][0]["classification"]
                    
                    final_label = classification_data.get("label", "manual_review")
                    confidence = classification_data.get("confidence", 0.5)
                    entities = classification_data.get("entities", {})
                    
                    print(f"✅ Classification Complete:")
                    print(f"   📋 Label: {final_label}")
                    print(f"   📊 Confidence: {confidence:.2f}")
                    print(f"   ⏱️ Time: {classification_time:.3f}s")
                    
                else:
                    print(f"❌ Classification API failed: {response.status_code}")
                    final_label = "manual_review"
                    confidence = 0.3
                    entities = {}
                    classification_data = {"error": f"API error: {response.status_code}"}
                    
            except Exception as e:
                print(f"❌ Classification API call failed: {e}")
                final_label = "manual_review"
                confidence = 0.3
                entities = {}
                classification_data = {"error": str(e)}
                classification_time = 0
            
            # Step 2: Call Reply Generation API (if needed)
            print("🔍 Step 2: Calling reply generation API...")
            reply_result = None
            
            # Only generate replies for labels that need them
            reply_labels = ["invoice_request_no_info", "claims_paid_no_proof"]
            
            if final_label in reply_labels:
                try:
                    reply_payload = {
                        "subject": subject,
                        "body": body,
                        "label": final_label,
                        "entities": entities
                    }
                    
                    start_time = time.time()
                    response = requests.post(self.reply_url, json=reply_payload, timeout=30)
                    reply_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        reply_data = response.json()
                        reply_text = reply_data.get("reply", "")
                        template_used = reply_data.get("template_used", "")
                        
                        print(f"✅ Reply Generated:")
                        print(f"   📝 Template: {template_used}")
                        print(f"   📏 Length: {len(reply_text)} characters")
                        print(f"   ⏱️ Time: {reply_time:.3f}s")
                        print(f"   📄 Preview: {reply_text[:100]}...")
                        
                        reply_result = {
                            "reply": reply_text,
                            "template_used": template_used,
                            "generation_time": reply_time
                        }
                    else:
                        print(f"❌ Reply API failed: {response.status_code}")
                        reply_result = {"error": f"API error: {response.status_code}"}
                        
                except Exception as e:
                    print(f"❌ Reply API call failed: {e}")
                    reply_result = {"error": str(e)}
            else:
                print(f"ℹ️ No reply needed for label: {final_label}")
            
            # Compile result
            email_result = {
                "email_id": email_id,
                "subject": subject,
                "body": body,
                "classification": {
                    "final_label": final_label,
                    "confidence": confidence,
                    "processing_time": classification_time,
                    "entities": entities,
                    "full_result": classification_data
                },
                "reply_generation": reply_result,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(email_result)
            
            print(f"✅ Email #{email_id} processing complete")
            print("-" * 40)
        
        # Save results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"email_api_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print processing summary"""
        print("\n" + "="*60)
        print("📊 PROCESSING SUMMARY")
        print("="*60)
        
        total_emails = len(results)
        print(f"📧 Total Emails Processed: {total_emails}")
        
        # Label distribution
        label_counts = {}
        reply_counts = 0
        
        for result in results:
            label = result['classification']['final_label']
            label_counts[label] = label_counts.get(label, 0) + 1
            
            if result.get('reply_generation') and 'error' not in result['reply_generation']:
                reply_counts += 1
        
        print(f"💬 Replies Generated: {reply_counts}")
        print(f"\n📋 Label Distribution:")
        for label, count in sorted(label_counts.items()):
            percentage = (count / total_emails) * 100
            print(f"   {label}: {count} ({percentage:.1f}%)")
        
        # Average confidence
        confidences = [r['classification']['confidence'] for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        print(f"\n📊 Average Confidence: {avg_confidence:.2f}")
        
        print("="*60)

def main():
    """Main function to run the processor"""
    print("🚀 Email CSV API Tester Starting...")
    
    # HARDCODE YOUR CSV FILE PATH HERE
    csv_file_path = "inbox_emails_20250530_160726.csv"  # Change this to your CSV file path
    
    # Initialize API tester
    tester = SimpleCSVTester()
    
    # Process the CSV
    try:
        results = tester.process_csv(csv_file_path)
        print(f"\n🎉 Processing completed! Processed {len(results)} emails via API.")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()