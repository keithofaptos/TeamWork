import streamlit as st
import re
import socket
import tldextract
import concurrent.futures
import time

def extract_domains(text):
    domain_pattern = r'(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)'
    domains = re.findall(domain_pattern, text)
    cleaned_domains = [tldextract.extract(domain).registered_domain for domain in domains if tldextract.extract(domain).suffix]
    return list(set(cleaned_domains))

def check_domain(domain):
    try:
        socket.gethostbyname(domain)
        return f"{domain}: Registered (DNS record found)"
    except socket.gaierror:
        return f"{domain}: Likely Available (No DNS record found)"
    except Exception as e:
        return f"{domain}: Error ({str(e)})"

def run_domain_checker():
    st.title("🤷‍♀️  Domain Name Availability Checker")
    
    text = st.text_area("Enter a block of text containing domain names")
    
    if st.button("🧐 Check Availability"):
        if text:
            domains = extract_domains(text)
            
            if domains:
                st.subheader("Domain Availability Results:")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    future_to_domain = {executor.submit(check_domain, domain): domain for domain in domains}
                    for i, future in enumerate(concurrent.futures.as_completed(future_to_domain)):
                        result = future.result()
                        results.append(result)
                        progress = (i + 1) / len(domains)
                        progress_bar.progress(progress)
                        status_text.text(f"Processed {i+1}/{len(domains)} domains")
                        time.sleep(0.05)
                
                progress_bar.empty()
                status_text.empty()
                
                sorted_results = sorted(results, key=lambda x: (
                    "Error" in x,
                    "Registered" in x,
                    "Available" in x,
                    x
                ))
                
                st.table(sorted_results)
                st.balloons()
            else:
                st.write("No valid domain names found in the provided text.")
        else:
            st.write("Please enter a block of text containing domain names.")

if __name__ == "__main__":
    run_domain_checker()
