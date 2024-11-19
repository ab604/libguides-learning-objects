# Library website links
library(tidyverse)
library(glue)

# Read the data ----------------------------------------------------------------
#df <- read_csv("data/lib_links_report_2024-10-09.csv", na = c("","[]"))
df <- read_csv("data/external-links-report-2024-10-16.csv")

panopto_df <- read_csv("data/panopto/panopto-libskills-2024-10-14.csv") |> 
  janitor::clean_names()

# Count the HTTP status tags ---------------------------------------------------
df |> group_by(status) |> 
  tally()

# Filter for four types of LO --------------------------------------------------
dfm <- df |> 
  filter(str_detect(url,"[Aa]rticulate|[Tt]hinglink|[Wwo]rdpress|[Pp]anopto|[Pp]owtoon")) |> 
  mutate(lo = case_when(str_detect(url,"[Pp]anopto") ~ "Panopto",
                        str_detect(url,"thinglink") ~ "ThingLink",
                        str_detect(url,"[Ar]ticulate") ~ "Articulate",
                        str_detect(url,"[Ww]ordpress") ~ "Wordpress",
                        str_detect(url,"[Pp]owtoon") ~ "Powtoon",
                         TRUE ~ "Other"))

# Initial count ----------------------------------------------------------------
 dfm |> 
   group_by(lo) |> 
   tally()

# Get panopto  unique slugs ----------------------------------------------------
panopto <- dfm |> 
  filter(lo == "Panopto") |> 
  mutate(session_id = str_extract(url, "(?<=id=)[^&=]+")) 

# Get panopto session names
panopto_sessions <- panopto_df |> 
  select(session_id,session_name,folder_name,folder_id) |> 
  distinct(session_id, .keep_all = T)

# Join panopto tables, 67 unique videos
panopto_join <- panopto |> 
  left_join(panopto_sessions) |> 
  filter(str_detect(folder_name,"^LIBSKILLS"))

panopto_join |> group_by(session_name,session_id) |> 
  tally() |> 
  arrange(desc(n)) |> View()

panopto_join |> 
  select(session_name,state, panopto_url = url, 
    library_url = parent, session_id) |> 
  write_excel_csv(glue("panopto-library-website-{today()}.csv"))

# Thinglinks -------------------------------------------------------------------

View(dfm)
tl_num <- "\\b\\d{19}\\b"
pattern <- "(?:scenario(?:%2F|/))?\\b(\\d{19})\\b"

tl_match <- function(urls) {
  pattern <- "(?:scenario(?:%2F|/)|/)?(\\d{19})(?:\\b|&)"
  matches <- str_extract(urls, pattern)
  return(str_extract(matches, "\\d{19}"))
}

tls <- dfm |> 
  filter(lo == "ThingLink") |> 
  mutate(id = tl_match(url))

tls_filt <- tls |> 
  filter(str_detect(url,"card|scenario|scene")) 

ds_tls <- c("1877657037140132326","1877348233051636580","1877330329652429668",
"1877315949388890980","1734893194337845734","1605566995493814273")

tls_filt |> 
  filter(!(id %in% ds_tls)) |> 
  View()
## ---------------------------------------------------------------------------------

#az <- "https://library.soton.ac.uk/az"

#df |> 
 # filter(str_detect(url,az)) |> View()
 # group_by(status) |> 
 # tally()
