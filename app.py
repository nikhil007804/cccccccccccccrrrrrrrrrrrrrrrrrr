import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import pandas as pd
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="🔥 Advanced Web Scraper",
    page_icon="🌐",
    layout="wide"
)

# Session state
if 'crawl_results' not in st.session_state:
    st.session_state.crawl_results = pd.DataFrame()
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = []

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_base_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_page_data(url, soup, base_url):
    # Extract title
    title = soup.title.string if soup.title else "No title found"
    
    # Extract meta description
    meta_desc = ""
    meta_tag = soup.find('meta', attrs={'name': 'description'}) or \
               soup.find('meta', attrs={'property': 'og:description'})
    if meta_tag:
        meta_desc = meta_tag.get('content', '')
    
    # Extract headings
    headings = {}
    for i in range(1, 7):
        heading_tags = soup.find_all(f'h{i}')
        headings[f'h{i}'] = [clean_text(h.get_text()) for h in heading_tags]
    
    # Extract links (both internal and external)
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        is_internal = base_url in full_url
        links.append({
            'url': full_url,
            'text': clean_text(a.get_text()),
            'is_internal': is_internal
        })
    
    # Extract images
    images = [img.get('src', '') for img in soup.find_all('img')]
    
    # Extract main content text
    paragraphs = [clean_text(p.get_text()) for p in soup.find_all('p')]
    main_text = ' '.join(paragraphs)
    
    return {
        'url': url,
        'title': clean_text(title),
        'meta_description': clean_text(meta_desc),
        'headings': headings,
        'num_links': len(links),
        'num_images': len(images),
        'main_text': main_text,
        'links': links,
        'images': images,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def scrape_website(url, max_depth=1, max_pages=10):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        base_url = get_base_url(url)
        visited = set()
        to_visit = deque([(url, 0)])
        results = []
        
        with st.spinner("Crawling website..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while to_visit and len(results) < max_pages:
                current_url, depth = to_visit.popleft()
                
                if current_url in visited or depth > max_depth:
                    continue
                    
                try:
                    status_text.text(f"Crawling: {current_url}")
                    response = requests.get(current_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    if 'text/html' not in response.headers.get('content-type', ''):
                        continue
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_data = extract_page_data(current_url, soup, base_url)
                    results.append(page_data)
                    
                    # Add new links to queue
                    if depth < max_depth:
                        for link in page_data['links']:
                            if link['is_internal'] and link['url'] not in visited:
                                to_visit.append((link['url'], depth + 1))
                    
                    visited.add(current_url)
                    progress = min(100, int((len(results) / max_pages) * 100))
                    progress_bar.progress(progress)
                    
                    # Be nice to the server
                    time.sleep(1)
                    
                except Exception as e:
                    st.warning(f"Error processing {current_url}: {str(e)}")
                    continue
        
        status_text.empty()
        progress_bar.empty()
        
        if not results:
            return {
                'success': False,
                'error': 'No pages could be crawled',
                'data': []
            }
            
        return {
            'success': True,
            'data': results,
            'total_pages': len(results),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

def display_page_analysis(page_data):
    st.subheader("📄 Page Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Title", page_data['title'][:100] + ('...' if len(page_data['title']) > 100 else ''))
        st.metric("URL", page_data['url'])
        st.metric("Links Found", page_data['num_links'])
        
    with col2:
        st.metric("Images Found", page_data['num_images'])
        st.metric("Text Length", f"{len(page_data['main_text']):,} characters")
        st.metric("Crawled At", page_data['timestamp'])
    
    # Display meta description if available
    if page_data['meta_description']:
        with st.expander("📝 Meta Description"):
            st.write(page_data['meta_description'])
    
    # Display main content
    with st.expander("📄 Main Content"):
        st.text_area("", value=page_data['main_text'], height=300, key=f"content_{page_data['url']}")
    
    # Display headings
    with st.expander("📑 Headings"):
        for level in range(1, 7):
            if page_data['headings'].get(f'h{level}'):
                st.write(f"### H{level} Headings")
                for heading in page_data['headings'][f'h{level}']:
                    st.write(f"- {heading}")
    
    # Display links
    with st.expander("🔗 Links"):
        df_links = pd.DataFrame(page_data['links'])
        if not df_links.empty:
            st.dataframe(
                df_links[['url', 'text']].rename(columns={'url': 'URL', 'text': 'Link Text'}),
                use_container_width=True,
                height=300
            )
    
    # Display images
    if page_data['images']:
        with st.expander("🖼️ Images"):
            st.write(f"Found {len(page_data['images'])} images")
            for i, img in enumerate(page_data['images'][:5]):  # Show first 5 images
                st.image(urljoin(page_data['url'], img), caption=f"Image {i+1}", width=300)

def main():
    st.title("🌐 Advanced Web Scraper & Crawler")
    st.write("Extract and analyze content from any website with advanced crawling capabilities.")
    
    # Sidebar controls
    st.sidebar.header("Settings")
    max_depth = st.sidebar.slider("Crawl Depth", 0, 5, 1, 
                                 help="How many levels deep to crawl (0 = just the entered URL)")
    max_pages = st.sidebar.slider("Maximum Pages", 1, 100, 10,
                                 help="Maximum number of pages to crawl")
    
    # Main content
    url = st.text_input("Enter website URL to crawl:", 
                       placeholder="https://example.com",
                       key="crawl_url")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Scrape Single Page"):
            if not url:
                st.warning("Please enter a URL")
            elif not is_valid_url(url):
                st.error("Please enter a valid URL (include http:// or https://)")
            else:
                with st.spinner(f"Scraping {url}..."):
                    result = scrape_website(url, max_depth=0, max_pages=1)
                    if result['success'] and result['data']:
                        st.session_state.scraped_data = result['data']
                        st.session_state.current_view = 'single'
                        st.rerun()
    
    with col2:
        if st.button("🕷️ Start Crawling"):
            if not url:
                st.warning("Please enter a URL")
            elif not is_valid_url(url):
                st.error("Please enter a valid URL (include http:// or https://)")
            else:
                with st.spinner(f"Crawling {url} (max depth: {max_depth}, max pages: {max_pages})..."):
                    result = scrape_website(url, max_depth=max_depth, max_pages=max_pages)
                    if result['success']:
                        st.session_state.crawl_results = pd.DataFrame([{
                            'URL': page['url'],
                            'Title': page['title'],
                            'Links': page['num_links'],
                            'Images': page['num_images']
                        } for page in result['data']])
                        st.session_state.scraped_data = result['data']
                        st.session_state.current_view = 'crawl'
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error occurred')}")
    
    # Display results based on current view
    if 'current_view' in st.session_state and st.session_state.scraped_data:
        if st.session_state.current_view == 'single':
            st.success(f"✅ Successfully scraped 1 page!")
            display_page_analysis(st.session_state.scraped_data[0])
            
        elif st.session_state.current_view == 'crawl':
            st.success(f"✅ Successfully crawled {len(st.session_state.scraped_data)} pages!")
            
            # Show crawl summary
            st.subheader("📊 Crawl Summary")
            st.dataframe(
                st.session_state.crawl_results,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL"),
                    "Title": "Page Title",
                    "Links": "# Links",
                    "Images": "# Images"
                }
            )
            
            # Allow user to select a page to view details
            selected_page = st.selectbox(
                "Select a page to view details:",
                options=range(len(st.session_state.scraped_data)),
                format_func=lambda i: f"{st.session_state.scraped_data[i]['title']} - {st.session_state.scraped_data[i]['url']}"
            )
            
            if selected_page is not None:
                display_page_analysis(st.session_state.scraped_data[selected_page])
            
            # Export options
            st.download_button(
                label="📥 Export to CSV",
                data=st.session_state.crawl_results.to_csv(index=False).encode('utf-8'),
                file_name=f"crawl_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )

if __name__ == "__main__":
    main()
