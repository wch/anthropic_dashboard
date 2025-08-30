library(shiny)
source("shinyreact.R", local = TRUE)

# Generate sample data (existing)
sample_data <- data.frame(
  id = 1:8,
  age = c(25, 30, 35, 28, 32, 27, 29, 33),
  score = c(85.5, 92.1, 88.3, 88.7, 95.2, 81.9, 87.4, 90.6),
  category = c("A", "B", "A", "C", "B", "A", "C", "B")
)

# Generate dashboard data
monthly_data <- data.frame(
  month = month.abb[1:12],
  desktop = c(186, 305, 237, 173, 209, 214, 186, 305, 237, 173, 209, 214),
  mobile = c(80, 200, 120, 190, 130, 140, 80, 200, 120, 190, 130, 140),
  revenue = c(4500, 7200, 5800, 6100, 5400, 6800, 4900, 7500, 6200, 5700, 6300, 7100)
)

trend_data <- data.frame(
  date = seq(as.Date("2024-01-01"), by = "month", length.out = 12),
  users = cumsum(c(1200, 150, 200, 180, 220, 190, 210, 240, 180, 200, 190, 220)),
  revenue = cumsum(c(45000, 5200, 6800, 5400, 7200, 6100, 6900, 8100, 5800, 6700, 6400, 7800))
)

ui <- barePage(
  title = "Shiny + shadcn/ui Example",
  tags$head(
    tags$script(src = "main.js", type = "module"),
    tags$link(href = "main.css", rel = "stylesheet")
  ),
  tags$div(id = "root")
)

server <- function(input, output, session) {
  # === EXISTING OUTPUTS (keep all functionality) ===
  
  # Process text input
  output$processed_text <- renderText({
    text <- input$user_text %||% ""
    reversed_text <- paste(rev(strsplit(text, "")[[1]]), collapse = "")
    toupper(reversed_text)
  })

  # Calculate text length
  output$text_length <- renderText({
    text <- input$user_text %||% ""
    nchar(text)
  })

  output$button_response <- renderText({
    paste("Event received at:", as.character(Sys.time(), digits = 2))
  }) |>
    bindEvent(input$button_trigger) # Trigger on button events

  # Table data output
  output$table_data <- renderObject({
    sample_data
  })

  # Plot output
  output$plot1 <- renderPlot({
    plot(
      sample_data$age,
      sample_data$score,
      xlab = "Age",
      ylab = "Score",
      main = "Age vs Score",
      pch = 19,
      cex = 1.5
    )

    # Add a trend line
    abline(lm(score ~ age, data = sample_data), col = "red", lwd = 2)

    # Add grid
    grid()
  })
  
  # === NEW DASHBOARD OUTPUTS ===
  
  # KPI Stats
  output$total_users <- renderText({
    sum(trend_data$users, na.rm = TRUE)
  })
  
  output$total_revenue <- renderText({
    sum(monthly_data$revenue, na.rm = TRUE)
  })
  
  output$active_sessions <- renderText({
    sample(800:1200, 1)  # Simulated real-time data
  })
  
  output$conversion_rate <- renderText({
    round(runif(1, 2.5, 4.8), 1)  # Simulated conversion rate
  })
  
  # Chart data for dashboard
  output$monthly_chart_data <- renderObject({
    monthly_data
  })
  
  output$trend_chart_data <- renderObject({
    # Convert dates to strings for JSON serialization
    trend_data$date <- as.character(trend_data$date)
    trend_data
  })
  
  output$category_chart_data <- renderObject({
    # Aggregate sample data by category
    category_summary <- aggregate(score ~ category, data = sample_data, FUN = mean)
    category_summary$count <- table(sample_data$category)[category_summary$category]
    category_summary
  })
  
  # Activity feed data
  output$activity_feed <- renderObject({
    activities <- c(
      "New user registered",
      "Payment processed",
      "Report generated",
      "Data exported",
      "User logged in",
      "Settings updated"
    )
    
    data.frame(
      id = 1:5,
      activity = sample(activities, 5),
      timestamp = format(Sys.time() - runif(5, 0, 3600), "%H:%M:%S"),
      user = paste("User", sample(100:999, 5))
    )
  })
}

shinyApp(ui = ui, server = server)
