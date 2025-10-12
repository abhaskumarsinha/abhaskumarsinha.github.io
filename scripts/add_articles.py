#!/usr/bin/env python3
"""
Blog Article Generator
Generates HTML blog articles from JSON data files using a template structure.

Usage:
    python generate_blog.py <json_file> [options]
    
Examples:
    python generate_blog.py multimodal-ai.json
    python generate_blog.py multimodal-ai.json -t custom_template.html -o output/
    python generate_blog.py data.json -o blogs/article.html
"""

import json
import argparse
import os
from pathlib import Path
from typing import Dict, List, Any


class BlogGenerator:
    """Generate HTML blog articles from JSON data."""
    
    def __init__(self, template_file: str = "sample_blog.html"):
        """
        Initialize the blog generator.
        
        Args:
            template_file: Path to the HTML template file
        """
        self.template_file = template_file
        self.template_content = self._load_template()
    
    def _load_template(self) -> str:
        """Load the HTML template file."""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file '{self.template_file}' not found")
    
    def _load_json(self, json_file: str) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file '{json_file}' not found")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in '{json_file}': {e}")
    
    def _escape_html(self, text: str) -> str:
        """Escape special HTML characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def _generate_meta_section(self, data: Dict) -> str:
        """Generate the article metadata section."""
        return f"""                    <div class="article-meta">
                        <span><i class="fas fa-calendar"></i> {data.get('date', '')}</span>
                        <span><i class="fas fa-clock"></i> {data.get('readTime', '')}</span>
                        <span><i class="fas fa-eye"></i> {data.get('views', '')} views</span>
                    </div>"""
    
    def _generate_tags(self, tags: List[str]) -> str:
        """Generate the tags section."""
        tag_html = []
        for tag in tags:
            tag_html.append(f'                        <span class="tag">{self._escape_html(tag)}</span>')
        return '\n'.join(tag_html)
    
    def _generate_toc(self, toc_items: List[Dict]) -> str:
        """Generate table of contents."""
        toc_html = []
        for item in toc_items:
            toc_html.append(f'                            <li><a href="#{item["id"]}">{self._escape_html(item["title"])}</a></li>')
        return '\n'.join(toc_html)
    
    def _generate_math_block(self, label: str, content: str) -> str:
        """Generate a math equation block."""
        # Convert LaTeX delimiters for MathJax
        math_content = content.replace('\\(', '').replace('\\)', '')
        return f"""
                    <div class="math-block">
                        <div class="equation-label">{self._escape_html(label)}</div>
                        $${math_content}$$
                    </div>"""
    
    def _generate_code_block(self, label: str, content: str, language: str = "python") -> str:
        """Generate a code block with syntax highlighting."""
        # Basic syntax highlighting
        highlighted = self._apply_syntax_highlighting(content, language)
        
        icon = "fab fa-python" if language.lower() == "python" else "fas fa-code"
        
        return f"""
                    <div class="code-block">
                        <div class="code-label"><i class="{icon}"></i> {self._escape_html(label)}</div>
                        <button class="copy-code-btn" onclick="copyCode(this)"><i class="fas fa-copy"></i> Copy</button>
                        <pre><code>{highlighted}</code></pre>
                    </div>"""
    
    def _apply_syntax_highlighting(self, code: str, language: str) -> str:
        """Apply basic syntax highlighting to code."""
        if language.lower() != "python":
            return self._escape_html(code)
        
        # Python keywords
        keywords = ['import', 'from', 'def', 'class', 'return', 'if', 'else', 'elif', 
                   'for', 'while', 'try', 'except', 'with', 'as', 'pass', 'break', 
                   'continue', 'yield', 'lambda', 'global', 'nonlocal']
        
        lines = code.split('\n')
        highlighted_lines = []
        
        for line in lines:
            # Escape HTML first
            line = self._escape_html(line)
            
            # Highlight comments
            if '#' in line and not line.strip().startswith('"""'):
                parts = line.split('#', 1)
                line = parts[0] + '<span class="comment">#' + parts[1] + '</span>'
            
            # Highlight strings (simple implementation)
            import re
            # Single-quoted strings
            line = re.sub(r'(\'[^\']*\')', r'<span class="string">\1</span>', line)
            # Double-quoted strings
            line = re.sub(r'(\"[^\"]*\")', r'<span class="string">\1</span>', line)
            # Triple-quoted strings
            line = re.sub(r'(\"\"\"[^\"]*\"\"\")', r'<span class="string">\1</span>', line)
            
            # Highlight numbers
            line = re.sub(r'\b(\d+\.?\d*)\b', r'<span class="number">\1</span>', line)
            
            # Highlight keywords
            for keyword in keywords:
                line = re.sub(rf'\b({keyword})\b', r'<span class="keyword">\1</span>', line)
            
            # Highlight function names (simple heuristic)
            line = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', r'<span class="function">\1</span>(', line)
            
            highlighted_lines.append(line)
        
        return '\n'.join(highlighted_lines)
    
    def _generate_content_sections(self, sections: List[Dict]) -> str:
        """Generate the main article content from sections."""
        content_html = []
        
        for section in sections:
            section_type = section.get('type', '')
            
            if section_type == 'heading':
                level = section.get('level', 2)
                section_id = section.get('id', '')
                id_attr = f' id="{section_id}"' if section_id else ''
                content = self._escape_html(section.get('content', ''))
                content_html.append(f'                    <h{level}{id_attr}>{content}</h{level}>')
            
            elif section_type == 'paragraph':
                content = section.get('content', '')
                # Don't escape content as it may contain LaTeX
                content_html.append(f'                    <p>\n                        {content}\n                    </p>')
            
            elif section_type == 'math':
                label = section.get('label', '')
                math_content = section.get('content', '')
                content_html.append(self._generate_math_block(label, math_content))
            
            elif section_type == 'code':
                label = section.get('label', 'Code')
                code_content = section.get('content', '')
                language = section.get('language', 'python')
                content_html.append(self._generate_code_block(label, code_content, language))
        
        return '\n\n'.join(content_html)
    
    def _generate_author_section(self, author: Dict) -> str:
        """Generate the author information section."""
        name = author.get('name', '')
        initials = author.get('initials', 'AU')
        bio = author.get('bio', '')
        social = author.get('social', {})
        
        social_links = []
        if social.get('github'):
            social_links.append(f'                            <a href="{social["github"]}" target="_blank" title="GitHub">\n                                <i class="fab fa-github"></i>\n                            </a>')
        if social.get('linkedin'):
            social_links.append(f'                            <a href="{social["linkedin"]}" target="_blank" title="LinkedIn">\n                                <i class="fab fa-linkedin"></i>\n                            </a>')
        if social.get('email'):
            social_links.append(f'                            <a href="mailto:{social["email"]}" title="Email">\n                                <i class="fas fa-envelope"></i>\n                            </a>')
        if social.get('twitter'):
            social_links.append(f'                            <a href="{social["twitter"]}" target="_blank" title="Twitter">\n                                <i class="fab fa-twitter"></i>\n                            </a>')
        
        return f"""                <div class="author-section">
                    <div class="author-avatar">{initials}</div>
                    <div class="author-info">
                        <h4>{self._escape_html(name)}</h4>
                        <p>{self._escape_html(bio)}</p>
                        <div class="author-social">
{chr(10).join(social_links)}
                        </div>
                    </div>
                </div>"""
    
    def _generate_related_articles(self, articles: List[Dict]) -> str:
        """Generate related articles section."""
        cards_html = []
        
        for article in articles:
            title = self._escape_html(article.get('title', ''))
            excerpt = self._escape_html(article.get('excerpt', ''))
            date = article.get('date', '')
            link = article.get('id', '#')
            
            cards_html.append(f"""                        <div class="related-card">
                            <h4><a href="{link}.html">{title}</a></h4>
                            <p>{excerpt}</p>
                            <div class="related-card-meta">
                                <i class="fas fa-calendar"></i> {date}
                            </div>
                        </div>""")
        
        return '\n'.join(cards_html)
    
    def _generate_description(self, data: Dict, max_length: int = 160) -> str:
        """
        Generate SEO description from article content.
        
        Args:
            data: Article data dictionary
            max_length: Maximum description length
        
        Returns:
            SEO-optimized description
        """
        # Try to get first paragraph from sections
        sections = data.get('sections', [])
        description = ""
        
        for section in sections:
            if section.get('type') == 'paragraph':
                content = section.get('content', '')
                # Remove LaTeX and markdown
                import re
                content = re.sub(r'\$.*?\
    
    def generate(self, json_file: str, output_file: str = None, base_url: str = "https://abhaskumarsinha.github.io") -> str:
        """
        Generate HTML blog article from JSON data.
        
        Args:
            json_file: Path to input JSON file
            output_file: Path to output HTML file (optional)
            base_url: Base URL for SEO tags (default: https://abhaskumarsinha.github.io)
        
        Returns:
            Path to the generated HTML file
        """
        # Load JSON data
        data = self._load_json(json_file)
        
        # Determine output filename
        if output_file is None:
            base_name = Path(json_file).stem
            output_file = f"{base_name}.html"
        
        # Generate components
        title = data.get('title', 'Untitled Article')
        seo_tags = self._generate_seo_tags(data, base_url)
        meta_section = self._generate_meta_section(data)
        tags_section = self._generate_tags(data.get('tags', []))
        toc_section = self._generate_toc(data.get('tableOfContents', []))
        content_section = self._generate_content_sections(data.get('sections', []))
        author_section = self._generate_author_section(data.get('author', {}))
        related_section = self._generate_related_articles(data.get('relatedArticles', []))
        
        # Create HTML content (simplified - using core structure)
        html_content = self.template_content
        
        # Insert SEO tags after the viewport meta tag
        viewport_pos = html_content.find('<meta name="viewport"')
        viewport_end = html_content.find('>', viewport_pos) + 1
        html_content = html_content[:viewport_end] + '\n' + seo_tags + '\n' + html_content[viewport_end:]
        
        # Replace placeholders with actual content
        html_content = html_content.replace(
            '<title>The Future of Multimodal AI | Abhas Kumar Sinha</title>',
            f'<title>{self._escape_html(title)} | {self._escape_html(data.get("author", {}).get("name", ""))}</title>'
        )
        
        html_content = html_content.replace(
            '<h1 class="article-title">The Future of Multimodal AI: Bridging Vision and Language</h1>',
            f'<h1 class="article-title">{self._escape_html(title)}</h1>'
        )
        
        # Replace metadata
        old_meta = html_content[html_content.find('<div class="article-meta">'):html_content.find('</div>', html_content.find('<div class="article-meta">')) + 6]
        html_content = html_content.replace(old_meta, meta_section)
        
        # Replace tags
        old_tags = html_content[html_content.find('<div class="article-tags">'):html_content.find('</div>', html_content.find('<div class="article-tags">')) + 6]
        new_tags = f'                    <div class="article-tags">\n{tags_section}\n                    </div>'
        html_content = html_content.replace(old_tags, new_tags)
        
        # Replace TOC
        old_toc = html_content[html_content.find('<ul class="toc-list">'):html_content.find('</ul>', html_content.find('<ul class="toc-list">')) + 5]
        new_toc = f'                        <ul class="toc-list">\n{toc_section}\n                        </ul>'
        html_content = html_content.replace(old_toc, new_toc)
        
        # Replace article content
        content_start = html_content.find('<div class="article-content">')
        content_end = html_content.find('</div>', html_content.find('<!-- Share Section -->')) - 16
        old_content = html_content[content_start:content_end]
        new_content = f'                <div class="article-content">\n{content_section}\n                '
        html_content = html_content.replace(old_content, new_content)
        
        # Replace author section
        author_start = html_content.find('<!-- Author Section -->')
        author_end = html_content.find('<!-- Related Posts -->')
        old_author = html_content[author_start:author_end]
        new_author = f'<!-- Author Section -->\n{author_section}\n\n                '
        html_content = html_content.replace(old_author, new_author)
        
        # Replace related articles
        related_start = html_content.find('<div class="related-grid">')
        related_end = html_content.find('</div>', related_start) + 6
        old_related = html_content[related_start:related_end]
        new_related = f'<div class="related-grid">\n{related_section}\n                    </div>'
        html_content = html_content.replace(old_related, new_related)
        
        # Update share text in JavaScript
        html_content = html_content.replace(
            'const text = encodeURIComponent("The Future of Multimodal AI: Bridging Vision and Language");',
            f'const text = encodeURIComponent("{title.replace('"', '\\"')}");'
        )
        
        html_content = html_content.replace(
            'const subject = encodeURIComponent("Check out this article: The Future of Multimodal AI");',
            f'const subject = encodeURIComponent("Check out this article: {title.replace('"', '\\"')}");'
        )
        
        # Write output file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate HTML blog articles from JSON data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_blog.py multimodal-ai.json
  python generate_blog.py multimodal-ai.json -t custom_template.html
  python generate_blog.py data.json -o output/article.html
  python generate_blog.py data.json -u https://yourdomain.com
        """
    )
    
    parser.add_argument('json_file', help='Input JSON file containing article data')
    parser.add_argument('-t', '--template', default='sample_blog.html',
                       help='HTML template file (default: sample_blog.html)')
    parser.add_argument('-o', '--output', help='Output HTML file path (default: <json_name>.html)')
    parser.add_argument('-u', '--url', default='https://abhaskumarsinha.github.io',
                       help='Base URL for SEO tags (default: https://abhaskumarsinha.github.io)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        # Create generator
        generator = BlogGenerator(template_file=args.template)
        
        if args.verbose:
            print(f"Loading JSON data from: {args.json_file}")
            print(f"Using template: {args.template}")
            print(f"Base URL: {args.url}")
        
        # Generate HTML
        output_path = generator.generate(args.json_file, args.output, args.url)
        
        print(f"✓ Successfully generated: {output_path}")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except ValueError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
, '', content)  # Remove inline math
                content = re.sub(r'\\\(.*?\\\)', '', content)  # Remove LaTeX
                content = re.sub(r'\*\*.*?\*\*', '', content)  # Remove bold
                content = re.sub(r'\s+', ' ', content).strip()  # Normalize whitespace
                
                if content and len(content) > 50:
                    description = content
                    break
        
        # Truncate to max_length
        if len(description) > max_length:
            description = description[:max_length-3].rsplit(' ', 1)[0] + '...'
        
        return description or f"Read about {data.get('title', 'this article')} by {data.get('author', {}).get('name', 'the author')}."
    
    def _generate_seo_tags(self, data: Dict, base_url: str = "https://abhaskumarsinha.github.io") -> str:
        """
        Generate comprehensive SEO meta tags.
        
        Args:
            data: Article data dictionary
            base_url: Base URL for the website
        
        Returns:
            HTML string with all SEO tags
        """
        title = data.get('title', 'Untitled Article')
        author_name = data.get('author', {}).get('name', 'Abhas Kumar Sinha')
        author_social = data.get('author', {}).get('social', {})
        date = data.get('date', '')
        tags = data.get('tags', [])
        article_id = data.get('id', 'article')
        
        # Generate description
        description = self._generate_description(data)
        
        # Generate keywords from tags and title
        keywords = ', '.join(tags) if tags else 'AI, Machine Learning, Research'
        keywords += f', {author_name}'
        
        # Canonical URL
        canonical_url = f"{base_url}/{article_id}.html"
        
        # Social media image (can be customized)
        og_image = f"{base_url}/images/{article_id}-social.png"
        
        # Twitter handle (extract from twitter URL if available)
        twitter_handle = ""
        if author_social.get('twitter'):
            twitter_url = author_social['twitter']
            if '/' in twitter_url:
                twitter_handle = '@' + twitter_url.rstrip('/').split('/')[-1]
        
        seo_tags = f"""	<!-- SEO Meta Tags -->
	<meta name="description" content="{self._escape_html(description)}">
	<meta name="keywords" content="{self._escape_html(keywords)}">
	<meta name="author" content="{self._escape_html(author_name)}">
	<link rel="canonical" href="{canonical_url}">
	<meta name="robots" content="index, follow">
	<meta name="article:published_time" content="{self._convert_date_to_iso(date)}">
	<meta name="article:author" content="{self._escape_html(author_name)}">
	
	<!-- Open Graph Meta Tags -->
	<meta property="og:title" content="{self._escape_html(title)}">
	<meta property="og:description" content="{self._escape_html(description)}">
	<meta property="og:image" content="{og_image}">
	<meta property="og:url" content="{canonical_url}">
	<meta property="og:type" content="article">
	<meta property="og:site_name" content="{self._escape_html(author_name)}">
	<meta property="article:published_time" content="{self._convert_date_to_iso(date)}">
	<meta property="article:author" content="{self._escape_html(author_name)}">
	<meta property="article:section" content="{self._escape_html(tags[0]) if tags else 'Technology'}">
	<meta property="article:tag" content="{self._escape_html(', '.join(tags))}">
	
	<!-- Twitter Card Meta Tags -->
	<meta name="twitter:card" content="summary_large_image">
	<meta name="twitter:title" content="{self._escape_html(title)}">
	<meta name="twitter:description" content="{self._escape_html(description)}">
	<meta name="twitter:image" content="{og_image}">"""
        
        if twitter_handle:
            seo_tags += f'\n	<meta name="twitter:creator" content="{twitter_handle}">'
            seo_tags += f'\n	<meta name="twitter:site" content="{twitter_handle}">'
        
        # Generate JSON-LD structured data
        json_ld = self._generate_json_ld(data, canonical_url, author_social)
        
        seo_tags += f"""
	
	<!-- Structured Data (JSON-LD) -->
	<script type="application/ld+json">
{json_ld}
	</script>"""
        
        return seo_tags
    
    def _convert_date_to_iso(self, date_str: str) -> str:
        """
        Convert date string to ISO 8601 format.
        
        Args:
            date_str: Date string (e.g., "September 28, 2025")
        
        Returns:
            ISO formatted date string
        """
        if not date_str:
            return ""
        
        try:
            from datetime import datetime
            # Try parsing common formats
            formats = [
                "%B %d, %Y",  # September 28, 2025
                "%b %d, %Y",  # Sep 28, 2025
                "%Y-%m-%d",   # 2025-09-28
                "%m/%d/%Y",   # 09/28/2025
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
                except ValueError:
                    continue
            
            return ""
        except:
            return ""
    
    def _generate_json_ld(self, data: Dict, url: str, social: Dict) -> str:
        """
        Generate JSON-LD structured data for the article.
        
        Args:
            data: Article data dictionary
            url: Canonical URL
            social: Author social links
        
        Returns:
            JSON-LD string
        """
        title = data.get('title', 'Untitled Article')
        author_name = data.get('author', {}).get('name', 'Abhas Kumar Sinha')
        date = data.get('date', '')
        description = self._generate_description(data)
        tags = data.get('tags', [])
        
        # Build author same-as links
        same_as = []
        if social.get('github'):
            same_as.append(social['github'])
        if social.get('linkedin'):
            same_as.append(social['linkedin'])
        if social.get('twitter'):
            same_as.append(social['twitter'])
        
        same_as_json = ',\n        '.join([f'"{link}"' for link in same_as])
        keywords_json = ', '.join(tags)
        
        json_ld = f"""	{{
	  "@context": "https://schema.org",
	  "@type": "BlogPosting",
	  "headline": "{self._escape_html(title)}",
	  "description": "{self._escape_html(description)}",
	  "url": "{url}",
	  "datePublished": "{self._convert_date_to_iso(date)}",
	  "dateModified": "{self._convert_date_to_iso(date)}",
	  "author": {{
	    "@type": "Person",
	    "name": "{self._escape_html(author_name)}",
	    "url": "{url.rsplit('/', 1)[0]}/",
	    "sameAs": [
	      {same_as_json}
	    ],
	    "jobTitle": "PhD Researcher",
	    "worksFor": {{
	      "@type": "Organization",
	      "name": "IIT Guwahati"
	    }}
	  }},
	  "publisher": {{
	    "@type": "Person",
	    "name": "{self._escape_html(author_name)}"
	  }},
	  "keywords": "{self._escape_html(keywords_json)}",
	  "articleSection": "{self._escape_html(tags[0]) if tags else 'Technology'}",
	  "inLanguage": "en-US",
	  "mainEntityOfPage": {{
	    "@type": "WebPage",
	    "@id": "{url}"
	  }}
	}}"""
        
        return json_ld
    
    def generate(self, json_file: str, output_file: str = None) -> str:
        """
        Generate HTML blog article from JSON data.
        
        Args:
            json_file: Path to input JSON file
            output_file: Path to output HTML file (optional)
        
        Returns:
            Path to the generated HTML file
        """
        # Load JSON data
        data = self._load_json(json_file)
        
        # Determine output filename
        if output_file is None:
            base_name = Path(json_file).stem
            output_file = f"{base_name}.html"
        
        # Generate components
        title = data.get('title', 'Untitled Article')
        meta_section = self._generate_meta_section(data)
        tags_section = self._generate_tags(data.get('tags', []))
        toc_section = self._generate_toc(data.get('tableOfContents', []))
        content_section = self._generate_content_sections(data.get('sections', []))
        author_section = self._generate_author_section(data.get('author', {}))
        related_section = self._generate_related_articles(data.get('relatedArticles', []))
        
        # Create HTML content (simplified - using core structure)
        html_content = self.template_content
        
        # Replace placeholders with actual content
        html_content = html_content.replace(
            '<title>The Future of Multimodal AI | Abhas Kumar Sinha</title>',
            f'<title>{self._escape_html(title)} | {self._escape_html(data.get("author", {}).get("name", ""))}</title>'
        )
        
        html_content = html_content.replace(
            '<h1 class="article-title">The Future of Multimodal AI: Bridging Vision and Language</h1>',
            f'<h1 class="article-title">{self._escape_html(title)}</h1>'
        )
        
        # Replace metadata
        old_meta = html_content[html_content.find('<div class="article-meta">'):html_content.find('</div>', html_content.find('<div class="article-meta">')) + 6]
        html_content = html_content.replace(old_meta, meta_section)
        
        # Replace tags
        old_tags = html_content[html_content.find('<div class="article-tags">'):html_content.find('</div>', html_content.find('<div class="article-tags">')) + 6]
        new_tags = f'                    <div class="article-tags">\n{tags_section}\n                    </div>'
        html_content = html_content.replace(old_tags, new_tags)
        
        # Replace TOC
        old_toc = html_content[html_content.find('<ul class="toc-list">'):html_content.find('</ul>', html_content.find('<ul class="toc-list">')) + 5]
        new_toc = f'                        <ul class="toc-list">\n{toc_section}\n                        </ul>'
        html_content = html_content.replace(old_toc, new_toc)
        
        # Replace article content
        content_start = html_content.find('<div class="article-content">')
        content_end = html_content.find('</div>', html_content.find('<!-- Share Section -->')) - 16
        old_content = html_content[content_start:content_end]
        new_content = f'                <div class="article-content">\n{content_section}\n                '
        html_content = html_content.replace(old_content, new_content)
        
        # Replace author section
        author_start = html_content.find('<!-- Author Section -->')
        author_end = html_content.find('<!-- Related Posts -->')
        old_author = html_content[author_start:author_end]
        new_author = f'<!-- Author Section -->\n{author_section}\n\n                '
        html_content = html_content.replace(old_author, new_author)
        
        # Replace related articles
        related_start = html_content.find('<div class="related-grid">')
        related_end = html_content.find('</div>', related_start) + 6
        old_related = html_content[related_start:related_end]
        new_related = f'<div class="related-grid">\n{related_section}\n                    </div>'
        html_content = html_content.replace(old_related, new_related)
        
        # Update share text in JavaScript
        html_content = html_content.replace(
            'const text = encodeURIComponent("The Future of Multimodal AI: Bridging Vision and Language");',
            f'const text = encodeURIComponent("{title.replace('"', '\\"')}");'
        )
        
        html_content = html_content.replace(
            'const subject = encodeURIComponent("Check out this article: The Future of Multimodal AI");',
            f'const subject = encodeURIComponent("Check out this article: {title.replace('"', '\\"')}");'
        )
        
        # Write output file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate HTML blog articles from JSON data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_blog.py multimodal-ai.json
  python generate_blog.py multimodal-ai.json -t custom_template.html
  python generate_blog.py data.json -o output/article.html
        """
    )
    
    parser.add_argument('json_file', help='Input JSON file containing article data')
    parser.add_argument('-t', '--template', default='sample_blog.html',
                       help='HTML template file (default: sample_blog.html)')
    parser.add_argument('-o', '--output', help='Output HTML file path (default: <json_name>.html)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        # Create generator
        generator = BlogGenerator(template_file=args.template)
        
        if args.verbose:
            print(f"Loading JSON data from: {args.json_file}")
            print(f"Using template: {args.template}")
        
        # Generate HTML
        output_path = generator.generate(args.json_file, args.output)
        
        print(f"✓ Successfully generated: {output_path}")
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return 1
    except ValueError as e:
        print(f"✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
