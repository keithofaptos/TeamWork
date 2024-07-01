import streamlit as st
import whois
import re
import tldextract

def extract_domains(text):
    # Use regex to find all domain-like patterns in the text
    domain_pattern = r'(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+)'
    domains = re.findall(domain_pattern, text)
    
    # Use tldextract to clean and validate the domains
    cleaned_domains = [tldextract.extract(domain).registered_domain for domain in domains]
    
    return list(set(cleaned_domains))  # Return unique domains

def check_domain(domain):
    try:
        w = whois.whois(domain)
        if w.domain_name is None:
            return f"{domain}: Available"
        else:
            return f"{domain}: Purchased"
    except:
        return f"{domain}: Available"

def run_domain_checker():
    st.title("Domain Name Availability Checker")
    
    text = st.text_area("Enter a block of text containing domain names")
    
    if st.button("Check Availability"):
        if text:
            domains = extract_domains(text)
            
            if domains:
                st.subheader("Domain Availability Results:")
                results = []
                for domain in domains:
                    result = check_domain(domain)
                    results.append(result)
                
                st.table(results)
            else:
                st.write("No domain names found in the provided text.")
        else:
            st.write("Please enter a block of text.")

if __name__ == "__main__":
    run_domain_checker()
