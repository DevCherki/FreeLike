import requests
from bs4 import BeautifulSoup
from colorama import init, Fore, Style
import os
import time
from langdetect import detect

# تهيئة colorama
init(autoreset=True)

# قائمة بالكلمات التي تعني "إعجاب" بلغات مختلفة
reaction_words = {
    'en': 'Like',
    'ar': 'إعجاب',
    'es': 'Me gusta',
    'fr': 'J’aime',
    'de': 'Gefällt mir',
    # إضافة لغات أخرى حسب الحاجة
}

def print_banner():
    banner = f"""
{Fore.YELLOW}┌───────────────────────────────────────────────────┐
│                                                   │
│    {Fore.GREEN} ██████╗██╗  ██╗███████╗██████╗ ██╗  ██╗██╗    {Fore.YELLOW}│
│    {Fore.GREEN}██╔════╝██║  ██║██╔════╝██╔══██╗██║ ██╔╝██║    {Fore.YELLOW}│
│    {Fore.GREEN}██║     ███████║█████╗  ██████╔╝█████╔╝ ██║    {Fore.YELLOW}│
│    {Fore.GREEN}██║     ██╔══██║██╔══╝  ██╔══██╗██╔═██╗ ██║    {Fore.YELLOW}│
│    {Fore.GREEN}╚██████╗██║  ██║███████╗██║  ██║██║  ██╗██║    {Fore.YELLOW}│
│    {Fore.RED} ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝    {Fore.YELLOW}│
│                               {Fore.CYAN}Cherki Commenter 2.0{Fore.YELLOW}│
└───────────────────────────────────────────────────┘
    """
    print(banner)

def is_account_saved(username):
    if os.path.exists('data.txt'):
        with open('data.txt', 'r') as file:
            accounts = file.readlines()
            return username in accounts
    return False

def save_account(username, password):
    with open('data.txt', 'a') as file:
        file.write(f'{username}\n{password}\n')
    print(f'{Fore.GREEN}Account saved: {username}')

def login_to_facebook(username, password, retries=3):
    login_url = 'https://mbasic.facebook.com/login'
    session = requests.Session()

    for attempt in range(retries):
        try:
            login_page = session.get(login_url)
            soup = BeautifulSoup(login_page.text, 'html.parser')
            login_form = soup.find('form')

            if not login_form:
                print(f'{Fore.RED}Login form not found on attempt {attempt+1}!')
                continue

            data = {}
            for input_tag in login_form.find_all('input'):
                if input_tag.get('name'):
                    data[input_tag.get('name')] = input_tag.get('value')

            data['email'] = username
            data['pass'] = password

            post_url = login_form.get('action')
            if not post_url.startswith('http'):
                post_url = 'https://mbasic.facebook.com' + post_url

            response = session.post(post_url, data=data)

            if 'c_user' in session.cookies:
                print(f'{Fore.GREEN}Login successful for {username}!')
                if not is_account_saved(username):
                    save_account(username, password)
                return session.cookies
            else:
                print(f'{Fore.RED}Login failed for {username} on attempt {attempt+1}!')
        except Exception as e:
            print(f'{Fore.RED}Error during login attempt {attempt+1}: {str(e)}')

    print(f'{Fore.RED}Login failed for {username} after {retries} attempts.')
    return None

def post_comment(cookies, post_url, comment_text, reaction_text, comment_count=10, retries=3):
    post_url = post_url.replace('https://www.facebook.com/', 'https://mbasic.facebook.com/')

    for attempt in range(retries):
        try:
            response = requests.get(post_url, cookies=cookies)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                comment_form = soup.find('form', action=True, method="post")
                if comment_form:
                    comment_url = 'https://mbasic.facebook.com' + comment_form['action']
                    data = {
                        'fb_dtsg': comment_form.find('input', {'name': 'fb_dtsg'})['value'],
                        'jazoest': comment_form.find('input', {'name': 'jazoest'})['value'],
                        'comment_text': comment_text
                    }

                    for _ in range(comment_count):
                        comment_response = requests.post(comment_url, cookies=cookies, data=data)
                        if comment_response.status_code == 200:
                            print(f'{Fore.GREEN}Comment posted successfully!')
                        else:
                            print(f'{Fore.RED}Failed to post comment! {comment_response.status_code}')

                    # محاولة للتفاعل مع المنشور
                    for like_attempt in range(retries):
                        reaction_links = soup.find_all('a', href=True)
                        for link in reaction_links:
                            if link['href'].startswith('/a/like.php?'):
                                reaction_url = 'https://mbasic.facebook.com' + link['href']
                                reaction_response = requests.get(reaction_url, cookies=cookies)

                                if reaction_response.status_code == 200:
                                    print(f'{Fore.GREEN}The post has been reacted successfully!')
                                    return
                                else:
                                    print(f'{Fore.RED}Failed to react! Attempt {like_attempt+1}. {reaction_response.status_code}')
                            else:
                                print(f'{Fore.RED}No suitable reaction link found! Attempt {like_attempt+1}.')
                        print(f'{Fore.YELLOW}Retrying reaction attempt {like_attempt+1}...')
                        time.sleep(2)  # إضافة تأخير قبل المحاولة مرة أخرى

                    return
                else:
                    print(f'{Fore.RED}Comment form not found on page!')
            else:
                print(f'{Fore.RED}Failed to fetch post page! {response.status_code}')
        except Exception as e:
            print(f'{Fore.RED}Error during comment attempt {attempt+1}: {str(e)}')

        print(f'{Fore.YELLOW}Retrying comment attempt {attempt+1}...')
    
    print(f'{Fore.RED}Failed to post comment or react after {retries} attempts.')

def main():
    print_banner()

    # قراءة بيانات الحسابات من الملف
    if os.path.exists('data.txt'):
        with open('data.txt', 'r') as file:
            lines = file.readlines()
            accounts = [(lines[i].strip(), lines[i + 1].strip()) for i in range(0, len(lines), 2)]
    else:
        print(f'{Fore.RED}No accounts found in data.txt.')
        return

    post_url = input(f'{Fore.CYAN}Enter the post link: ')
    comment_text = input(f'{Fore.CYAN}Enter the comment text: ')
    reaction_text = input(f'{Fore.CYAN}Enter the reaction text (e.g., "Like" or any equivalent): ')

    for username, password in accounts:
        print(f'{Fore.CYAN}Processing account: {username}')
        cookies = login_to_facebook(username, password)
        if cookies:
            post_comment(cookies, post_url, comment_text, reaction_text)
        else:
            print(f'{Fore.RED}Login failed for {username}. Skipping.')

if __name__ == "__main__":
    main()
