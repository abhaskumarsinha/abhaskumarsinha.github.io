#!/usr/bin/env python3
"""
Blog Index Page Generator
Scans a folder for blog JSON files and updates blogs.html with all blog entries.

Usage:
    python update_blog_index.py <json_folder> -t <template_html> -o <output_html>
    python update_blog_index.py blogs/json -t blogs.html -o blogs.html
"""

import json
import argparse
import os
import re
from pathlib import Path
from datetime import datetime


class BlogIndexGenerator:
    def __init__(self, template_path):
        self.template_path = template_path
        self.template = None
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = f.read()
        else:
            raise FileNotFoundError(f"Template file not found: {template_path}")
    
    def load_blog_json_files(self, json_folder):
        """Load all JSON files from the specified folder"""
        json_files = []
        folder_path = Path(json_folder)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"JSON folder not found: {json_folder}")
        
        # Find all .json files
        for json_file in folder_path.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_filename'] = json_file.stem  # Store filename without extension
                    json_files.append(data)
                    print(f"✓ Loaded: {json_file.name}")
            except Exception as e:
                print(f"✗ Error loading {json_file.name}: {str(e)}")
        
        return json_files
    
    def parse_date(self, date_str):
        """Parse date string to datetime object for sorting"""
        try:
            for fmt in ['%B %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return datetime.now()
        except:
            return datetime.now()
    
    def sort_blogs_by_date(self, blogs):
        """Sort blogs by date (newest first)"""
        return sorted(blogs, key=lambda x: self.parse_date(x.get('date', '')), reverse=True)
    
    def extract_excerpt(self, sections, max_length=200):
        """Extract excerpt from blog sections"""
        for section in sections:
            if section.get('type') == 'paragraph':
                content = section.get('content', '')
                # Remove LaTeX and special characters
                content = re.sub(r'\\\(.*?\\\)', '', content)
                content = re.sub(r'\$.*?\$', '', content)
                content = content.strip()
                if len(content) > max_length:
                    content = content[:max_length].rsplit(' ', 1)[0] + '...'
                return content
        return "Read more about this topic..."
    
    def categorize_blog(self, tags):
        """Determine primary category from tags"""
        tag_map = {
            'ai': ['AI & ML', 'AI', 'Machine Learning', 'Deep Learning', 'Neural Networks'],
            'research': ['Research', 'Paper', 'Study', 'NLP', 'Computer Vision'],
            'tutorial': ['Tutorial', 'Guide', 'How-to', 'PyTorch', 'TensorFlow'],
            'insights': ['Insights', 'Personal', 'Thoughts', 'Opinion', 'Ethics']
        }
        
        tags_lower = [tag.lower() for tag in tags]
        for category, keywords in tag_map.items():
            for keyword in keywords:
                if any(keyword.lower() in tag for tag in tags_lower):
                    return category
        
        return 'ai'  # Default category
    
    def format_views(self, views_str):
        """Format views string consistently"""
        if isinstance(views_str, int):
            if views_str >= 1000:
                return f"{views_str/1000:.1f}k"
            return str(views_str)
        
        # If already a string, clean it up
        views_str = str(views_str).replace(',', '').replace(' views', '').replace('views', '').strip()
        try:
            views_num = int(views_str)
            if views_num >= 1000:
                return f"{views_num/1000:.1f}k"
            return str(views_num)
        except:
            return views_str
    
    def generate_blog_article_html(self, blog, index=0, is_featured=False):
        """Generate HTML for a single blog article"""
        blog_id = blog.get('id', blog.get('_filename', 'blog'))
        title = blog.get('title', 'Untitled Blog Post')
        date = blog.get('date', 'Date Unknown')
        read_time = blog.get('readTime', 'N/A')
        views = self.format_views(blog.get('views', '0'))
        tags = blog.get('tags', [])
        tags_str = ', '.join(tags[:2]) if tags else 'General'
        
        # Extract excerpt
        excerpt = self.extract_excerpt(blog.get('sections', []))
        
        # Determine category
        category = self.categorize_blog(tags)
        
        # Calculate shares (mock calculation based on views)
        try:
            views_num = int(views.replace('k', '00').replace('.', ''))
            shares = int(views_num * 0.06)  # ~6% share rate
        except:
            shares = 0
        
        # Format blog URL
        blog_url = f"blogs/{blog_id}.html"
        
        # Featured badge
        featured_badge = ''
        featured_class = ''
        if is_featured:
            featured_badge = '\n                    <span class="featured-badge"><i class="fas fa-star"></i> Featured</span>'
            featured_class = ' featured'
        
        html = f'''                <article class="list-item{featured_class}" data-category="{category}">
{featured_badge}                    <div class="list-item-content">
                        <h3><a href="{blog_url}">{title}</a></h3>
                        <p class="list-item-excerpt">{excerpt}</p>
                        <div class="list-item-meta">
                            <span><i class="fas fa-calendar"></i> {date}</span>
                            <span><i class="fas fa-clock"></i> {read_time}</span>
                            <span><i class="fas fa-tag"></i> {tags_str}</span>
                        </div>
                        <div class="blog-stats">
                            <span class="stat-item"><i class="fas fa-eye"></i> {views} views</span>
                            <span class="stat-item"><i class="fas fa-share"></i> {shares} shares</span>
                        </div>
                        <a href="{blog_url}" class="read-more">Read Full Article <i class="fas fa-arrow-right"></i></a>
                    </div>
                </article>

'''
        return html
    
    def extract_all_categories(self, blogs):
        """Extract all unique categories from blogs"""
        categories = set()
        for blog in blogs:
            tags = blog.get('tags', [])
            category = self.categorize_blog(tags)
            categories.add(category)
        
        # Always include these base categories
        base_categories = ['all', 'ai', 'research', 'tutorial', 'insights']
        return base_categories
    
    def generate_category_filters(self, categories):
        """Generate category filter buttons HTML"""
        html = ''
        category_names = {
            'all': 'All',
            'ai': 'AI & ML',
            'research': 'Research',
            'tutorial': 'Tutorials',
            'insights': 'Insights'
        }
        
        for i, category in enumerate(categories):
            active_class = ' active' if category == 'all' else ''
            display_name = category_names.get(category, category.title())
            html += f'                    <button class="category-filter{active_class}" onclick="filterCategory(\'{category}\')">{display_name}</button>\n'
        
        return html.rstrip()
    
    def generate_blogs_list_html(self, blogs):
        """Generate complete blogs list HTML"""
        if not blogs:
            return '''                <article class="list-item">
                    <div class="list-item-content">
                        <h3>No Blog Posts Available</h3>
                        <p class="list-item-excerpt">Check back soon for new content!</p>
                    </div>
                </article>'''
        
        html = ''
        # First blog is featured
        for i, blog in enumerate(blogs):
            is_featured = (i == 0)
            html += self.generate_blog_article_html(blog, i, is_featured)
        
        return html.rstrip()
    
    def update_blogs_html(self, blogs, output_path):
        """Update blogs.html with all blog entries"""
        if not self.template:
            raise ValueError("Template not loaded")
        
        # Sort blogs by date
        sorted_blogs = self.sort_blogs_by_date(blogs)
        
        print(f"\n📊 Processing {len(sorted_blogs)} blog posts...")
        
        # Generate category filters
        categories = self.extract_all_categories(sorted_blogs)
        category_filters_html = self.generate_category_filters(categories)
        
        # Generate blogs list
        blogs_list_html = self.generate_blogs_list_html(sorted_blogs)
        
        # Update template
        html = self.template
        
        # Replace category filters
        category_section_start = html.find('<div class="blog-categories">')
        category_section_end = html.find('</div>', category_section_start) + 6
        
        new_category_section = f'''<div class="blog-categories">
{category_filters_html}
                </div>'''
        
        html = html[:category_section_start] + new_category_section + html[category_section_end:]
        
        # Replace blog posts list
        list_start = html.find('<div class="content-list">')
        list_end = html.find('</div>', html.find('<!-- Subscribe Section -->'))
        
        new_list_section = f'''<div class="content-list">
{blogs_list_html}
            </div>'''
        
        html = html[:list_start] + new_list_section + html[list_end:]
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✓ Successfully updated: {output_path}")
        print(f"  - Total blogs: {len(sorted_blogs)}")
        print(f"  - Categories: {', '.join(categories)}")
        print(f"  - Featured: {sorted_blogs[0].get('title', 'N/A') if sorted_blogs else 'None'}")
        
        # Print blog summary
        print("\n📝 Blog Posts Summary:")
        for i, blog in enumerate(sorted_blogs, 1):
            status = "⭐ FEATURED" if i == 1 else f"   #{i}"
            print(f"  {status} - {blog.get('title', 'Untitled')} ({blog.get('date', 'N/A')})")
    
    def generate_blog_summary_json(self, blogs, output_path):
        """Generate a summary JSON file with all blog metadata"""
        summary = {
            "total_blogs": len(blogs),
            "last_updated": datetime.now().isoformat(),
            "blogs": []
        }
        
        for blog in blogs:
            blog_summary = {
                "id": blog.get('id', blog.get('_filename', '')),
                "title": blog.get('title', ''),
                "date": blog.get('date', ''),
                "tags": blog.get('tags', []),
                "readTime": blog.get('readTime', ''),
                "views": blog.get('views', ''),
                "url": f"blogs/{blog.get('id', blog.get('_filename', ''))}.html"
            }
            summary["blogs"].append(blog_summary)
        
        summary_path = os.path.join(os.path.dirname(output_path), 'blog_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Generated blog summary: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate blog index page from JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python update_blog_index.py blogs/json -t blogs.html -o blogs.html
  python update_blog_index.py ./json_folder -t templates/blogs.html -o public/blogs.html
  python update_blog_index.py blogs/json --summary
        '''
    )
    
    parser.add_argument('json_folder', help='Folder containing blog JSON files')
    parser.add_argument('-t', '--template', required=True, help='Template blogs.html file')
    parser.add_argument('-o', '--output', required=True, help='Output blogs.html file')
    parser.add_argument('--summary', action='store_true', help='Generate blog summary JSON file')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.json_folder):
        print(f"Error: JSON folder not found: {args.json_folder}")
        return 1
    
    if not os.path.exists(args.template):
        print(f"Error: Template file not found: {args.template}")
        return 1
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created output directory: {output_dir}")
    
    try:
        # Generate blog index
        print(f"🔍 Scanning for blog JSON files in: {args.json_folder}")
        print("─" * 60)
        
        generator = BlogIndexGenerator(args.template)
        blogs = generator.load_blog_json_files(args.json_folder)
        
        if not blogs:
            print("\n⚠ Warning: No blog JSON files found!")
            return 1
        
        print("─" * 60)
        generator.update_blogs_html(blogs, args.output)
        
        # Generate summary if requested
        if args.summary:
            generator.generate_blog_summary_json(blogs, args.output)
        
        print("\n✅ Blog index generation complete!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
