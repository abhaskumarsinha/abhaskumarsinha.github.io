import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

class SitemapGenerator:
    def __init__(self, base_url, output_dir="."):
        """
        Initialize the sitemap generator.
        
        Args:
            base_url: The base URL of your website (e.g., 'https://example.com')
            output_dir: Directory to save the sitemap file
        """
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.pages = []
        self.gallery_images = []
        
    def crawl_html_pages(self, start_path="."):
        """Crawl HTML files in the directory."""
        html_files = list(Path(start_path).rglob("*.html"))
        
        for html_file in html_files:
            # Convert file path to URL path
            rel_path = os.path.relpath(html_file, start_path)
            url_path = rel_path.replace(os.sep, '/')
            
            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(html_file))
            
            self.pages.append({
                'loc': urljoin(self.base_url, url_path),
                'lastmod': mod_time.strftime('%Y-%m-%d'),
                'changefreq': 'weekly',
                'priority': '1.0' if 'index.html' in url_path else '0.8',
                'is_gallery': 'gallery.html' in url_path.lower()
            })
        
        print(f"Found {len(self.pages)} HTML pages")
    
    def load_gallery_json(self, json_path="./images/gallery.json"):
        """Load and process gallery.json to extract image information."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                gallery_data = json.load(f)
            
            for item in gallery_data:
                # Get the image paths
                image_path = item.get('image', '')
                thumb_path = item.get('thumbnail', '')
                
                # Add full image
                if image_path:
                    self.gallery_images.append({
                        'loc': urljoin(self.base_url, image_path),
                        'title': item.get('title', ''),
                        'caption': item.get('description', ''),
                        'geo_location': item.get('location', '')
                    })
                
                # Add thumbnail
                if thumb_path and thumb_path != image_path:
                    self.gallery_images.append({
                        'loc': urljoin(self.base_url, thumb_path),
                        'title': f"{item.get('title', '')} (Thumbnail)",
                        'caption': item.get('description', ''),
                        'geo_location': item.get('location', '')
                    })
            
            print(f"Loaded {len(self.gallery_images)} images from gallery.json")
            
        except FileNotFoundError:
            print(f"Warning: {json_path} not found")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {json_path}")
    
    def _escape_xml(self, text):
        """Escape special XML characters."""
        if not text:
            return ''
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
    
    def generate_unified_sitemap(self):
        """Generate a single sitemap.xml with all pages and images."""
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        
        # Add all pages
        for page in self.pages:
            url = SubElement(urlset, 'url')
            
            # Add page location
            loc = SubElement(url, 'loc')
            loc.text = self._escape_xml(page['loc'])
            
            # Add last modified date
            lastmod = SubElement(url, 'lastmod')
            lastmod.text = page['lastmod']
            
            # Add change frequency
            changefreq = SubElement(url, 'changefreq')
            changefreq.text = page['changefreq']
            
            # Add priority
            priority = SubElement(url, 'priority')
            priority.text = page['priority']
            
            # If this is the gallery page, add all images
            if page['is_gallery'] and self.gallery_images:
                for img in self.gallery_images:
                    image = SubElement(url, 'image:image')
                    
                    # Image location (required)
                    image_loc = SubElement(image, 'image:loc')
                    image_loc.text = self._escape_xml(img['loc'])
                    
                    # Image title (optional but recommended)
                    if img.get('title'):
                        image_title = SubElement(image, 'image:title')
                        image_title.text = self._escape_xml(img['title'])
                    
                    # Image caption (optional but recommended)
                    if img.get('caption'):
                        image_caption = SubElement(image, 'image:caption')
                        image_caption.text = self._escape_xml(img['caption'])
                    
                    # Geographic location (optional)
                    if img.get('geo_location'):
                        image_geo = SubElement(image, 'image:geo_location')
                        image_geo.text = self._escape_xml(img['geo_location'])
        
        return self._prettify_xml(urlset)
    
    def _prettify_xml(self, elem):
        """Return a pretty-printed XML string."""
        rough_string = tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        # Remove extra blank lines
        lines = [line for line in pretty.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def save_sitemap(self):
        """Generate and save the sitemap file."""
        sitemap_xml = self.generate_unified_sitemap()
        sitemap_path = os.path.join(self.output_dir, 'sitemap.xml')
        
        with open(sitemap_path, 'w', encoding='utf-8', newline='\n') as f:
            # Write clean XML declaration
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            # Skip the XML declaration from prettify_xml and write content
            content = '\n'.join(sitemap_xml.split('\n')[1:])
            f.write(content)
        
        print(f"\n✓ Generated {sitemap_path}")
        
        # Print summary
        page_count = len(self.pages)
        image_count = len(self.gallery_images)
        print(f"\nSitemap contains:")
        print(f"  - {page_count} web pages")
        print(f"  - {image_count} images")
        print(f"  - Total URLs: {page_count}")
    
    def run(self):
        """Run the complete sitemap generation process."""
        print("=" * 60)
        print("Starting Single Sitemap Generation")
        print("=" * 60)
        
        # Crawl HTML pages
        print("\n[1/3] Crawling HTML pages...")
        self.crawl_html_pages()
        
        # Load gallery data
        print("\n[2/3] Loading gallery data...")
        self.load_gallery_json()
        
        # Save sitemap
        print("\n[3/3] Generating sitemap...")
        self.save_sitemap()
        
        print("\n" + "=" * 60)
        print("✓ Sitemap generation complete!")
        print("=" * 60)
        print(f"\nNext steps:")
        print(f"1. Upload sitemap.xml to your website root")
        print(f"2. Add to robots.txt:")
        print(f"   Sitemap: {self.base_url}/sitemap.xml")
        print(f"3. Submit to Google Search Console:")
        print(f"   {self.base_url}/sitemap.xml")
        print()


if __name__ == "__main__":
    # Configuration
    BASE_URL = "https://abhaskumarsinha.github.io/"  # Change this to your actual website URL
    
    # Create generator and run
    generator = SitemapGenerator(BASE_URL)
    generator.run()
