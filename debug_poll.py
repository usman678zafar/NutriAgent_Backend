import requests
import os

def test_pollinations():
    url = "https://image.pollinations.ai/prompt/test%20food%20image?width=400&height=600&model=turbo&seed=123"
    print(f"Downloading from {url}")
    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            with open("test_poll.jpg", "wb") as f:
                f.write(response.content)
            print(f"File saved to {os.path.abspath('test_poll.jpg')}")
            print(f"Size: {len(response.content)} bytes")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_pollinations()
