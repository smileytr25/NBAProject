import time

def wait_for_rate_limit(page_limit, pages_visited, start_time):
    if pages_visited == page_limit:
        wait_time = max(0, 60 - (time.time() - start_time))
        print(f"Rate limited. Waiting {wait_time:.2f} seconds")

        time.sleep(wait_time)
        return 0, time.time()

    return pages_visited, start_time
