import math

__author__ = 'Raghav'


class Pagination:
    """
    Represents a pagination object.
    Takes 3 arguments. Total result count, current page number and results to be displayed per page i.e limit.
    """
    # If there's a next page
    has_next = True

    # If there's a previous page
    has_previous = True

    # Current page number
    current_page = None

    # Total number of pages. This is also the last page number. (Obviously)
    total_pages = None

    # Total number of results.
    total_results = None

    # Number of results to display per page.
    limit = None

    # A list of page numbers to display in pagination bar for navigation.
    page_numbers = []

    def __init__(self, total_results, current_page, limit=50):
        self.total_results = total_results
        self.total_pages = max(int(math.ceil(total_results/limit)), 1)

        # Displays the content of last page if current_page is greater than total number of pages.
        # Or content of first page if it's less than 1
        if current_page < 1:
            self.current_page = 1
        elif current_page > self.total_pages:
            self.current_page = self.total_pages
        else:
            self.current_page = current_page

        self.limit = limit

        if self.current_page == 1:
            self.has_previous = False
        if self.current_page == self.total_pages:
            self.has_next = False

        start = max(self.current_page - 4, 1)
        end = min(self.current_page + 4, self.total_pages)

        self.page_numbers = range(start, end + 1)