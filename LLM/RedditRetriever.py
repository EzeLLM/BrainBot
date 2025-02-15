import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

def get_reddit_trends(subreddits=['memes','news'], exclude_keywords=['gaming', 'keyboard']):
    """
    Fetches top posts from specified subreddits, filtered by keywords
    Requires Reddit API credentials (free tier available)
    
    Parameters:
    subreddits (list): List of subreddits to monitor
    exclude_keywords (list): Keywords to filter out
    
    Returns:
    list: Top 10 trending post titles with metadata
    """
    
    # Reddit API credentials
    CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    SECRET = os.getenv('REDDIT_SECRET')
    
    # Authenticate with Reddit API
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET)
    data = {'grant_type': 'client_credentials'}
    headers = {'User-Agent': 'ContentTrendFinder/1.0'}
    
    # Get OAuth token
    response = requests.post('https://www.reddit.com/api/v1/access_token',
                            auth=auth, data=data, headers=headers)
    token = response.json().get('access_token')
    headers = {**headers, 'Authorization': f'bearer {token}'}
    
    # Fetch posts from combined subreddits
    subreddit_str = '+'.join(subreddits)
    response = requests.get(
        f'https://oauth.reddit.com/r/{subreddit_str}/hot',
        headers=headers,
        params={'limit': 100, 't': 'day'}
    )
    
    trends = []
    if response.status_code == 200:
        posts = response.json()['data']['children']
        for post in posts:
            post_data = post['data']
            title = post_data['title'].lower()
            
            # Filter out excluded keywords
            if any(kw in title for kw in [k.lower() for k in exclude_keywords]):
                continue
                
            trends.append({
                'title': post_data['title'],
                'upvotes': post_data['ups'],
                'url': post_data['url'],
                'subreddit': post_data['subreddit'],
                'created_utc': datetime.utcfromtimestamp(post_data['created_utc'])
            })
    
    # Sort by upvotes and return top 10
    return sorted(trends, key=lambda x: x['upvotes'], reverse=True)[:10]

# Example usage
if __name__ == "__main__":
    trends = get_reddit_trends(
        subreddits=['politics', 'worldnews'],
        exclude_keywords=['gaming', 'keyboard']
    )
    
    print("Top Trending Reddit Posts:")
    for i, post in enumerate(trends, 1):
        print(f"{i}. [{post['subreddit']}] {post['title']}")
        print(f"   Upvotes: {post['upvotes']} | Posted: {post['created_utc']}")
        print(f"   URL: {post['url']}\n")