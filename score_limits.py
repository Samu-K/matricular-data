import scrapy
from scrapy.linkextractors import LinkExtractor

class ScoreLimitsSpider(scrapy.Spider):
    name = 'score_limits'
    allowed_domains = ['www.ylioppilastutkinto.fi']
    start_urls = ['https://www.ylioppilastutkinto.fi/ylioppilastutkinto/pisterajat/']

    # This determines what we do with the first URL
    def parse(self, response):
      
        # Define the LinkExtractor
        le = LinkExtractor(
            allow_domains=self.allowed_domains,
            # We select the sidebar with our wanted links
            restrict_xpaths='//*[@id="sidebar"]/div[1]/nav/ul/li[5]/div',
        )

        # We then run through each link that we fetched
        for link in le.extract_links(response):

            # We run a scrapy request on each link
            yield scrapy.Request(
                url=link.url,
                # Callback is where we tell the spyder what do in in the given url
                callback=self.parse_table,
                # We can give the callback the date so we can use it in the parsing
                # link.text returns the text where the link was hyperlinked on the website
                # In this case that means we get the year and season
                cb_kwargs={ 'date': link.text },
            )

    # Setup the function to parse through each found link
    def parse_table(self, response, date):

        # We find the table on the site (only one) and get the table rows
        rows = response.css('#content table tbody tr')

        # If rows is empty, there's no table on the site
        if not rows:
            print(f'No table found for url: {response.url}')
            # We return just that statement
            return
        
        # Categories describes what grade in what order the numbers in the table are
        # They are essentially the column names
        categories = [
          char.root.text for char \
          # This selectes the entire table, including column names
          in response.css('#content table'). \
          # Selects the first row
          css('tr')[0]. \
          # Selects the text found in the first row
          # First value is empty so we skip that
          css('td')[1:]
        ]

        # The websites have differing td types
        # If td type is strong, then the previous list comprehension won't work
        if None in categories:
          categories = [
            char.root.text for char \
            in response.css('#content table'). \
            css('tr')[0]. \
            # We run through the same way, but use strong as the added selector at the end
            # We also don't need the [1:], since first value is not empty in these
            css('td strong')
          ]
        
        # We start from the seocond row to avoid column header row
        for row in rows[1:]:
            # We select the data in that row
            cols = row.css('td')
            # First value is always the name of the subject
            title = cols[0].root.text
            # The rest of the value are the grade points
            nums = [col.root.text for col in cols[1:]]

            # Setup the final dict we'll yield
            data = {
                "title": title,
                "date": date,
            }

            # We start at 0 for first value
            x=0
            
            # By going thorugh each number, we can place in order
            # First number will match the first category and so forth
            for num in nums:
              # We add the number to the data with correct category
              data[categories[x]] = num
              # Move onto the next category as we move onto the next number
              x +=1

            # We then yield the data
            # Each yield gives us the data for one subject
            yield data

