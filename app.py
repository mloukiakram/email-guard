import re
import subprocess
import html
import random
import string
import uuid
from datetime import datetime
from flask import Flask, render_template, request

app = Flask(__name__)

# --- CLASS: ADVANCED TAG ENGINE ---
class TagEngine:
    def __init__(self):
        # 1. Cache for consistent tags (Session Scope)
        self.cache = {
            'sr': f"sl{random.randint(1000,9999)}",
            'ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'domaine': f"server-update-{random.randint(100,999)}.com",
            'name': f"user{random.randint(100,999)}",
            'to': f"target.test.{random.randint(1000,9999)}@gmail.com",
            'date': datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0500"),
            'boundaries': {} 
        }

    def _generate_random(self, mode, length):
        length = int(length)
        chars = ""
        if mode == 'A': chars = string.ascii_letters + string.digits       
        elif mode == 'C': chars = string.ascii_letters                     
        elif mode == 'L': chars = string.ascii_lowercase + string.digits   
        elif mode == 'LU': chars = string.ascii_uppercase + string.digits  
        elif mode == 'N': chars = string.digits                            
        elif mode == 'CL': chars = string.ascii_lowercase                  
        elif mode == 'CLU': chars = string.ascii_uppercase                 
        elif mode == 'CS': chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"            
        else: chars = string.ascii_letters + string.digits 
        
        return ''.join(random.choice(chars) for _ in range(length))

    def parse(self, text):
        if not text: return ""

        text = text.replace("[sr]", self.cache['sr'])
        text = text.replace("[ip]", self.cache['ip'])
        text = text.replace("[domaine]", self.cache['domaine'])
        text = text.replace("[Name]", self.cache['name'])
        text = text.replace("[*to]", self.cache['to'])
        text = text.replace("[*date]", self.cache['date'])
        
        # Legacy
        text = text.replace("[random]", self._generate_random('A', 18))

        # Dynamic Boundaries (EE:...)
        def repl_ee(m):
            key = m.group(1)
            if key not in self.cache['boundaries']:
                # Generate a random boundary string
                self.cache['boundaries'][key] = f"----=_Part_{self._generate_random('N', 5)}_{self._generate_random('A', 10)}"
            return self.cache['boundaries'][key]
        
        text = re.sub(r'\(EE([0-9]*):([^\)]+)\)', repl_ee, text) # Handles (EE1:...)

        # Regex for [RandomX/N]
        def repl_complex(m): return self._generate_random(m.group(1), m.group(2))
        text = re.sub(r'\[Random\((A|C|L|LU|N|CL|CLU|CS)\)/(\d+)\]', repl_complex, text)
        
        def repl_simple(m): return self._generate_random(m.group(1), m.group(2))
        text = re.sub(r'\[Random(A|C|L|LU|N|CL|CLU|CS)/(\d+)\]', repl_simple, text)

        return text

# --- HELPER: TEMPLATE FIXER (GOLD STANDARD) ---
def fix_template(raw_header, raw_body):
    """
    Replaces the user's header with the GOLD STANDARD template, 
    preserving Subject/From Name, and wrapping the body correctly.
    """
    
    # 1. Extract existing metadata (if any) to preserve it
    subject = "Welcome to the Community" # Default
    from_name = "Support Team"           # Default
    
    # Try to find Subject
    subj_match = re.search(r'^Subject:\s*(.+)$', raw_header, re.MULTILINE | re.IGNORECASE)
    if subj_match: subject = subj_match.group(1).strip()

    # Try to find From Name (e.g. From: "Akram" <...>)
    from_match = re.search(r'^From:\s*"?([^"<]+)"?', raw_header, re.MULTILINE | re.IGNORECASE)
    if from_match: from_name = from_match.group(1).strip()

    # 2. Define the Gold Standard Header Template
    # We use multipart/alternative instead of report to ensure body renders, 
    # but keep your structure.
    boundary_tag = "(EE1:[RandomA/69])"
    
    new_header = f"""Received: from efianalytics.com (efianalytics.com. 216.244.76.116)
Subject: {subject}
From: "{from_name}" <[RandomL/12]@[RandomCL/8].com>
Sender: <[RandomL/12]@[RandomL/6].pxwfashing.info>
Date: [*date]
To: <[*to]>
Message-Id: <[RandomA/23]-[RandomA/24]@[RandomA/15]>
List-Unsubscribe: <[RandomA/28]-[RandomA/27]@pxwfashing.info>
X-EMMAIL: [*to]@[domaine]
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="{boundary_tag}" """

    # 3. Wrap the Body with the matching Boundary
    # We inject the Plain Text version automatically too
    new_body = f"""--{boundary_tag}
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 7bit

[Plain Text Version of Message]

--{boundary_tag}
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: 7bit

{raw_body}

--{boundary_tag}--"""

    return new_header, new_body, "Applied Gold Standard Template (efianalytics)"

# --- SPAM PARSER ---
def parse_spam_report(report_text):
    rules = []
    score = 0.0
    if not report_text: return 0.0, []
    
    match = re.search(r'Content analysis details:\s+\(([\d.-]+) points', report_text)
    if match: 
        try: score = float(match.group(1))
        except: pass

    pattern = r'^\s*(-?\d+\.?\d*)\s+([A-Z0-9_]+)\s+(.*)$'
    matches = re.findall(pattern, report_text, re.MULTILINE)
    
    for points_str, name, desc in matches:
        try: points = float(points_str)
        except: continue
        
        severity = "info"
        if name == "INVALID_DATE": severity = "critical"
        elif name == "MSGID_FROM_MTA_HEADER": severity = "critical"
        elif points >= 1.0: severity = "warning"
        
        rules.append({"points": points, "name": name, "desc": desc.strip(), "severity": severity})

    return score, rules

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    simulated_source = None
    fixed_header = None
    fixed_body = None
    fix_log = None
    
    in_header = request.form.get('header_source', '')
    in_body = request.form.get('body_source', '')

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'scan':
            engine = TagEngine()
            full_template = f"{in_header.strip()}\n\n{in_body.strip()}"
            simulated_source = engine.parse(full_template)
            
            with open("temp_sim.eml", "w", encoding="utf-8") as f:
                f.write(simulated_source)
            
            try:
                proc = subprocess.run(['spamassassin', '-t', 'temp_sim.eml'], capture_output=True, text=True)
                score, rules = parse_spam_report(proc.stdout)
                
                status, color = "SAFE", "green"
                if score >= 5.0: status, color = "BLOCKED", "red"
                elif score >= 0.1: status, color = "ATTENTION", "orange"

                result = {"score": score, "rules": rules, "status": status, "color": color}
            except Exception as e:
                result = {"error": str(e)}

        elif action == 'fix':
            fixed_header, fixed_body, fix_log = fix_template(in_header, in_body)
            result = {"status": "FIXED", "rules": []}

    return render_template('index.html', result=result, in_header=in_header, in_body=in_body, 
                           simulated_source=simulated_source, fixed_header=fixed_header, 
                           fixed_body=fixed_body, fix_log=fix_log)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)