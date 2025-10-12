#!/usr/bin/env python3
"""
Blog Article Generator
Generates HTML blog articles from JSON files with auto-generated SEO tags.

Usage:
    python add_articles.py <json_file> -o <output_html> -t <template_html>
    python add_articles.py multimodal-ai.json -o multimodal-ai.html -t sample_blog.html
"""

import json
import argparse
import os
import re
from datetime import datetime
from pathlib import Path


class BlogGenerator:
    def __init__(self, template_path=None):
        self.template_path = template_path
        self.template = None
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
    
    def load_json(self, json_path):
        """Load blog data from JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def generate_seo_tags(self, data, base_url="https://abhaskumarsinha.github.io"):
        """Generate SEO meta tags from blog data"""
        title = data.get('title', '')
        author_name = data.get('author', {}).get('name', 'Abhas Kumar Sinha')
        
        # Create description from first paragraph or excerpt
        description = ""
        for section in data.get('sections', []):
            if section.get('type') == 'paragraph':
                description = section.get('content', '')[:160]
                # Remove LaTeX and special characters
                description = re.sub(r'\\\(.*?\\\)', '', description)
                description = re.sub(r'\$.*?\$', '', description)
                description = description.strip()
                break
        
        if not description:
            description = f"Read {title} by {author_name}"
        
        # Generate keywords from tags
        tags = data.get('tags', [])
        keywords = ', '.join(tags + [author_name, 'AI', 'Machine Learning', 'Research', 'Blog'])
        
        # Blog post URL
        blog_id = data.get('id', 'blog-post')
        canonical_url = f"{base_url}/blogs/{blog_id}.html"
        image_url = f"{base_url}/social_media_card.png"
        
        # Generate SEO tags HTML
        seo_tags = f'''
    <!-- SEO Meta Tags -->
    <meta name="description" content="{self.escape_html(description)}">
    <meta name="keywords" content="{self.escape_html(keywords)}">
    <link rel="canonical" href="{canonical_url}">
    <meta name="robots" content="index, follow">
    <meta name="author" content="{author_name}">
    <meta name="article:published_time" content="{self.parse_date(data.get('date', ''))}">
    <meta name="article:author" content="{author_name}">
    {self.generate_article_tags(tags)}
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{self.escape_html(title)} | {author_name}">
    <meta property="og:description" content="{self.escape_html(description)}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="{author_name}">
    <meta property="article:author" content="{author_name}">
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{self.escape_html(title)}">
    <meta name="twitter:description" content="{self.escape_html(description)}">
    <meta name="twitter:image" content="{image_url}">
    <meta name="twitter:creator" content="@{data.get('author', {}).get('twitter', '').replace('https://twitter.com/', '')}">
    
    <!-- Structured Data (JSON-LD) -->
    <script type="application/ld+json">
    {self.generate_structured_data(data, canonical_url)}
    </script>'''
        
        return seo_tags
    
    def escape_html(self, text):
        """Escape HTML special characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def parse_date(self, date_str):
        """Parse date string to ISO format"""
        try:
            # Try different date formats
            for fmt in ['%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()
    
    def generate_article_tags(self, tags):
        """Generate article:tag meta tags"""
        return '\n    '.join([f'<meta property="article:tag" content="{tag}">' for tag in tags])
    
    def generate_structured_data(self, data, url):
        """Generate JSON-LD structured data"""
        author = data.get('author', {})
        structured_data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": data.get('title', ''),
            "url": url,
            "datePublished": self.parse_date(data.get('date', '')),
            "author": {
                "@type": "Person",
                "name": author.get('name', 'Abhas Kumar Sinha'),
                "url": "https://abhaskumarsinha.github.io/",
                "sameAs": [
                    author.get('social', {}).get('github', ''),
                    author.get('social', {}).get('linkedin', '')
                ]
            },
            "publisher": {
                "@type": "Organization",
                "name": author.get('name', 'Abhas Kumar Sinha'),
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://abhaskumarsinha.github.io/social_media_card.png"
                }
            },
            "keywords": ', '.join(data.get('tags', [])),
            "articleSection": data.get('tags', [])[0] if data.get('tags') else "Technology"
        }
        return json.dumps(structured_data, indent=2)
    
    def generate_toc_html(self, toc_items):
        """Generate Table of Contents HTML"""
        html = ''
        for item in toc_items:
            html += f'                            <li><a href="#{item["id"]}">{item["title"]}</a></li>\n'
        return html
    
    def generate_content_html(self, sections):
        """Generate article content HTML from sections"""
        html = ''
        
        for section in sections:
            section_type = section.get('type')
            
            if section_type == 'heading':
                level = section.get('level', 2)
                section_id = section.get('id', '')
                content = section.get('content', '')
                html += f'                    <h{level} id="{section_id}">{content}</h{level}>\n'
            
            elif section_type == 'paragraph':
                content = section.get('content', '')
                html += f'                    <p>\n                        {content}\n                    </p>\n\n'
            
            elif section_type == 'math':
                label = section.get('label', '')
                content = section.get('content', '')
                display = section.get('display', True)
                
                if display:
                    html += f'''                    <div class="math-block">
                        <div class="equation-label">{label}</div>
                        $${content}$$
                    </div>\n\n'''
                else:
                    html += f'\\({content}\\)'
            
            elif section_type == 'code':
                label = section.get('label', 'Code')
                language = section.get('language', 'python')
                content = section.get('content', '')
                
                # Apply syntax highlighting
                highlighted = self.apply_syntax_highlighting(content, language)
                
                html += f'''                    <div class="code-block">
                        <div class="code-label"><i class="fab fa-python"></i> {label}</div>
                        <button class="copy-code-btn" onclick="copyCode(this)"><i class="fas fa-copy"></i> Copy</button>
                        <pre><code>{highlighted}</code></pre>
                    </div>\n\n'''
        
        return html
    
    def apply_syntax_highlighting(self, code, language):
        """Apply basic syntax highlighting"""
        if language.lower() == 'python':
            # Keywords
            keywords = ['import', 'from', 'as', 'def', 'class', 'return', 'if', 'else', 'elif',
                       'for', 'while', 'try', 'except', 'with', 'lambda', 'yield', 'pass', 'break',
                       'continue', 'raise', 'assert', 'del', 'global', 'nonlocal', 'and', 'or', 'not']
            
            for keyword in keywords:
                code = re.sub(rf'\b({keyword})\b', r'<span class="keyword">\1</span>', code)
            
            # Functions
            code = re.sub(r'(\w+)\(', r'<span class="function">\1</span>(', code)
            
            # Strings
            code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\'|".*?"|\'.*?\')', r'<span class="string">\1</span>', code, flags=re.DOTALL)
            
            # Comments
            code = re.sub(r'(#.*?)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
            
            # Numbers
            code = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="number">\1</span>', code)
        
        return code
    
    def generate_tags_html(self, tags):
        """Generate tags HTML"""
        html = ''
        for tag in tags:
            html += f'                        <span class="tag">{tag}</span>\n'
        return html
    
    def generate_related_articles_html(self, related):
        """Generate related articles HTML"""
        html = ''
        for article in related:
            html += f'''                        <div class="related-card">
                            <h4><a href="#">{article.get("title", "")}</a></h4>
                            <p>{article.get("excerpt", "")}</p>
                            <div class="related-card-meta">
                                <i class="fas fa-calendar"></i> {article.get("date", "")}
                            </div>
                        </div>\n'''
        return html
    
    def generate_html(self, data, output_path):
        """Generate complete HTML file"""
        if not self.template:
            raise ValueError("Template not loaded. Please provide a valid template file.")
        
        # Generate SEO tags
        seo_tags = self.generate_seo_tags(data)
        
        # Replace title
        html = self.template.replace(
            '<title>The Future of Multimodal AI | Abhas Kumar Sinha</title>',
            f'<title>{data.get("title", "")} | {data.get("author", {}).get("name", "Abhas Kumar Sinha")}</title>'
        )
        
        # Insert SEO tags after <title>
        title_end = html.find('</title>') + len('</title>')
        html = html[:title_end] + '\n' + seo_tags + '\n' + html[title_end:]
        
        # Replace article title
        html = html.replace(
            '<h1 class="article-title">The Future of Multimodal AI: Bridging Vision and Language</h1>',
            f'<h1 class="article-title">{data.get("title", "")}</h1>'
        )
        
        # Replace metadata
        author = data.get('author', {})
        html = html.replace(
            '<span><i class="fas fa-calendar"></i> September 28, 2025</span>',
            f'<span><i class="fas fa-calendar"></i> {data.get("date", "")}</span>'
        )
        html = html.replace(
            '<span><i class="fas fa-clock"></i> 12 min read</span>',
            f'<span><i class="fas fa-clock"></i> {data.get("readTime", "")}</span>'
        )
        html = html.replace(
            '<span><i class="fas fa-eye"></i> 2,456 views</span>',
            f'<span><i class="fas fa-eye"></i> {data.get("views", "0 views")}</span>'
        )
        
        # Replace tags
        tags_section = html[html.find('<div class="article-tags">'):html.find('</div>', html.find('<div class="article-tags">')) + 6]
        new_tags = f'''<div class="article-tags">
{self.generate_tags_html(data.get("tags", []))}                    </div>'''
        html = html.replace(tags_section, new_tags)
        
        # Replace TOC
        toc_list = html[html.find('<ul class="toc-list">'):html.find('</ul>', html.find('<ul class="toc-list">')) + 5]
        new_toc = f'''<ul class="toc-list">
{self.generate_toc_html(data.get("tableOfContents", []))}                        </ul>'''
        html = html.replace(toc_list, new_toc)
        
        # Replace content
        content_start = html.find('<div class="article-content">')
        content_end = html.find('</div>', html.find('<!-- Share Section -->')) 
        new_content = f'''<div class="article-content">
{self.generate_content_html(data.get("sections", []))}                </div>'''
        html = html[:content_start] + new_content + html[content_end:]
        
        # Replace author section
        html = html.replace(
            '<h4>Abhas Kumar Sinha</h4>',
            f'<h4>{author.get("name", "Abhas Kumar Sinha")}</h4>'
        )
        html = html.replace(
            '<p>PhD Researcher at IIT Guwahati specializing in AI and Computer Vision. Passionate about exploring the intersections of machine learning, computer vision, and their real-world applications.</p>',
            f'<p>{author.get("bio", "")}</p>'
        )
        
        # Replace related articles
        related_start = html.find('<div class="related-grid">')
        related_end = html.find('</div>', related_start) + 6
        new_related = f'''<div class="related-grid">
{self.generate_related_articles_html(data.get("relatedArticles", []))}                    </div>'''
        html = html[:related_start] + new_related + html[related_end:]
        
        # Update share text
        html = re.sub(
            r'const text = encodeURIComponent\(".*?"\);',
            f'const text = encodeURIComponent("{data.get("title", "")}");',
            html
        )
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ Successfully generated: {output_path}")
        print(f"  - Title: {data.get('title', '')}")
        print(f"  - Author: {author.get('name', '')}")
        print(f"  - Sections: {len(data.get('sections', []))}")
        print(f"  - SEO tags: Auto-generated")


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML blog articles from JSON files with SEO tags',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python add_articles.py blog.json -o output.html -t template.html
  python add_articles.py multimodal-ai.json -o blogs/multimodal-ai.html
        '''
    )
    
    parser.add_argument('json_file', help='Input JSON file containing blog data')
    parser.add_argument('-o', '--output', required=True, help='Output HTML file path')
    parser.add_argument('-t', '--template', help='Template HTML file (optional, uses sample_blog.html in same dir as json if not specified)')
    parser.add_argument('-u', '--base-url', default='https://abhaskumarsinha.github.io',
                       help='Base URL for canonical links (default: https://abhaskumarsinha.github.io)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.json_file):
        print(f"Error: JSON file not found: {args.json_file}")
        return 1
    
    # Find template
    template_path = args.template
    if not template_path:
        # Try to find sample_blog.html in the same directory as JSON
        json_dir = os.path.dirname(args.json_file)
        template_path = os.path.join(json_dir, 'sample_blog.html')
        if not os.path.exists(template_path):
            print(f"Error: Template file not found: {template_path}")
            print("Please specify template with -t option")
            return 1
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created output directory: {output_dir}")
    
    # Generate blog
    try:
        generator = BlogGenerator(template_path)
        data = generator.load_json(args.json_file)
        generator.generate_html(data, args.output)
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
