import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom import minidom

class SitemapGenerator:
    def __init__(self, base_url, output_dir="."):
        """
        Initialize the sitemap generator.
        
        Args:
            base_url: The base URL of your website (e.g., 'https://example.com')
            output_dir: Directory to save the sitemap files
        """
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.pages = []
        self.images = []
        
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
                'priority': '1.0' if 'index.html' in url_path else '0.8'
            })
    
    def load_gallery_json(self, json_path="./images/gallery.json"):
        """Load and process gallery.json to extract image information."""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                gallery_data = json.load(f)
            
            for item in gallery_data:
                # Get the image paths
                image_path = item.get('image', '')
                thumb_path = item.get('thumbnail', '')
                
                # Create image entries for both full and thumbnail
                if image_path:
                    self.images.append({
                        'loc': urljoin(self.base_url, image_path),
                        'title': item.get('title', ''),
                        'caption': item.get('description', ''),
                        'geo_location': item.get('location', ''),
                        'license': urljoin(self.base_url, 'license.html') if os.path.exists('license.html') else None
                    })
                
                if thumb_path:
                    self.images.append({
                        'loc': urljoin(self.base_url, thumb_path),
                        'title': f"{item.get('title', '')} (Thumbnail)",
                        'caption': item.get('description', ''),
                        'geo_location': item.get('location', ''),
                        'license': urljoin(self.base_url, 'license.html') if os.path.exists('license.html') else None
                    })
            
            print(f"Loaded {len(self.images)} images from gallery.json")
            
        except FileNotFoundError:
            print(f"Warning: {json_path} not found")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {json_path}")
    
    def generate_sitemap(self):
        """Generate the main sitemap.xml with pages."""
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        for page in self.pages:
            url = SubElement(urlset, 'url')
            
            loc = SubElement(url, 'loc')
            loc.text = page['loc']
            
            lastmod = SubElement(url, 'lastmod')
            lastmod.text = page['lastmod']
            
            changefreq = SubElement(url, 'changefreq')
            changefreq.text = page['changefreq']
            
            priority = SubElement(url, 'priority')
            priority.text = page['priority']
        
        return self._prettify_xml(urlset)
    
    def generate_image_sitemap(self):
        """Generate the image sitemap with detailed image information."""
        urlset = Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        
        # Group images by gallery page
        gallery_url = urljoin(self.base_url, 'gallery.html')
        if os.path.exists('gallery.html'):
            url = SubElement(urlset, 'url')
            loc = SubElement(url, 'loc')
            loc.text = gallery_url
            
            # Add all images under the gallery page
            for img in self.images:
                image = SubElement(url, 'image:image')
                
                image_loc = SubElement(image, 'image:loc')
                image_loc.text = img['loc']
                
                if img['title']:
                    image_title = SubElement(image, 'image:title')
                    image_title.text = img['title']
                
                if img['caption']:
                    image_caption = SubElement(image, 'image:caption')
                    image_caption.text = img['caption']
                
                if img['geo_location']:
                    image_geo = SubElement(image, 'image:geo_location')
                    image_geo.text = img['geo_location']
                
                if img.get('license'):
                    image_license = SubElement(image, 'image:license')
                    image_license.text = img['license']
        
        return self._prettify_xml(urlset)
    
    def generate_sitemap_index(self):
        """Generate sitemap index that references all sitemaps."""
        sitemapindex = Element('sitemapindex')
        sitemapindex.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Add main sitemap
        sitemap = SubElement(sitemapindex, 'sitemap')
        loc = SubElement(sitemap, 'loc')
        loc.text = urljoin(self.base_url, 'sitemap.xml')
        lastmod = SubElement(sitemap, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')
        
        # Add image sitemap
        sitemap = SubElement(sitemapindex, 'sitemap')
        loc = SubElement(sitemap, 'loc')
        loc.text = urljoin(self.base_url, 'sitemap-images.xml')
        lastmod = SubElement(sitemap, 'lastmod')
        lastmod.text = datetime.now().strftime('%Y-%m-%d')
        
        return self._prettify_xml(sitemapindex)
    
    def _prettify_xml(self, elem):
        """Return a pretty-printed XML string."""
        rough_string = tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def save_sitemaps(self):
        """Generate and save all sitemap files."""
        # Generate main sitemap
        sitemap_xml = self.generate_sitemap()
        sitemap_path = os.path.join(self.output_dir, 'sitemap.xml')
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_xml)
        print(f"✓ Generated {sitemap_path}")
        
        # Generate image sitemap
        image_sitemap_xml = self.generate_image_sitemap()
        image_sitemap_path = os.path.join(self.output_dir, 'sitemap-images.xml')
        with open(image_sitemap_path, 'w', encoding='utf-8') as f:
            f.write(image_sitemap_xml)
        print(f"✓ Generated {image_sitemap_path}")
        
        # Generate sitemap index
        sitemap_index_xml = self.generate_sitemap_index()
        sitemap_index_path = os.path.join(self.output_dir, 'sitemap-index.xml')
        with open(sitemap_index_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_index_xml)
        print(f"✓ Generated {sitemap_index_path}")
    
    def run(self):
        """Run the complete sitemap generation process."""
        print("Starting sitemap generation...")
        print("-" * 50)
        
        # Crawl HTML pages
        print("Crawling HTML pages...")
        self.crawl_html_pages()
        print(f"Found {len(self.pages)} pages")
        
        # Load gallery data
        print("\nLoading gallery data...")
        self.load_gallery_json()
        
        # Save all sitemaps
        print("\nGenerating sitemaps...")
        self.save_sitemaps()
        
        print("-" * 50)
        print("✓ Sitemap generation complete!")
        print(f"\nNext steps:")
        print(f"1. Upload sitemap files to your website root")
        print(f"2. Add to robots.txt:")
        print(f"   Sitemap: {self.base_url}/sitemap-index.xml")
        print(f"3. Submit to Google Search Console")


if __name__ == "__main__":
    # Configuration
    BASE_URL = "https://abhaskumarsinha.github.io/"  # Change this to your website URL
    
    # Create generator and run
    generator = SitemapGenerator(BASE_URL)
    generator.run()
