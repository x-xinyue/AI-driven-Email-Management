import sqlite3
import json


mock_data = [
  {
    "id": 1,
    "sender": "McDonald's Malaysia <crm@mcdonalds.com.my>",
    "subject": "Exclusive: RM10 off your favorite McChicken Meal!",
    "body_snippet": "Hi Xin Yue, we noticed you haven't had a burger in a while. Use code MCD10 at any outlet in Subang Jaya!",
    "unsubscribe_url": "https://unsubscribe.mcdonalds.com.my/token123",
    "status": "Unprocessed"
  },
  {
    "id": 2,
    "sender": "KFC Deals <promo@kfc.com.my>",
    "subject": "The 9-Piece Bucket is BACK! 🍗",
    "body_snippet": "Get your fried chicken fix today. Only RM35.90 for a limited time. Finger lickin' good deals inside.",
    "unsubscribe_url": "https://kfc.com.my/opt-out/user987",
    "status": "Unprocessed"
  },
  {
    "id": 3,
    "sender": "LinkedIn <notifications-noreply@linkedin.com>",
    "subject": "5 new jobs for 'Data Scientist' in Kuala Lumpur",
    "body_snippet": "NielsenIQ and Shopee are looking for candidates like you. See the latest postings based on your profile.",
    "unsubscribe_url": "https://www.linkedin.com/e/v2/unsubscribe",
    "status": "Unprocessed"
  },
  {
    "id": 4,
    "sender": "Shopee Malaysia <no-reply@shopee.com.my>",
    "subject": "9.9 Sale! Everything must go! 🚀",
    "body_snippet": "Don't miss out on the biggest sale of the year. Claim your RM0 shipping vouchers now before they expire.",
    "unsubscribe_url": "https://shopee.com.my/settings/unsubscribe",
    "status": "Unprocessed"
  },
  {
    "id": 5,
    "sender": "Maybank2u <alerts@maybank.com.my>",
    "subject": "Your Credit Card E-Statement is Ready",
    "body_snippet": "Your statement for the month of April 2026 is now available for viewing on Maybank2u. Please log in to download.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 6,
    "sender": "KFC Malaysia <news@kfc.com.my>",
    "subject": "Colonel's Monthly Newsletter: New Zinger Burger",
    "body_snippet": "Have you tried the new Zinger? It's crunchier, spicier, and waiting for you at Sunway Pyramid.",
    "unsubscribe_url": "https://kfc.com.my/opt-out/newsletter-unsubscribe",
    "status": "Unprocessed"
  },
  {
    "id": 7,
    "sender": "Grab Malaysia <marketing@grab.com>",
    "subject": "RM5 off your next ride to Sunway University! 🚗",
    "body_snippet": "Feeling lazy? We got you. Grab a ride from Subang Jaya to Sunway for less. Valid for 3 days.",
    "unsubscribe_url": "https://www.grab.com/my/unsubscribe",
    "status": "Unprocessed"
  },
  {
    "id": 8,
    "sender": "MR D.I.Y. Recruitment <hr-talent@mrdiy.com.my>",
    "subject": "Interview Invitation: Data Analyst Position",
    "body_snippet": "Dear Xin Yue, thank you for your interest in MR D.I.Y. We would like to invite you for a technical interview at our headquarters to discuss your Spark-Kafka experience.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 9,
    "sender": "NielsenIQ Talent Acquisition <careers.global@nielseniq.com>",
    "subject": "Update regarding your application",
    "body_snippet": "Thank you for completing the assessment. Our team is currently reviewing your Python and SQL results. We will get back to you within 5 working days.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 10,
    "sender": "Ticketmaster MY <noreply@ticketmaster.com.my>",
    "subject": "Your Tickets for Post Malone: A Brief Inquiry into Online Relationships Tour",
    "body_snippet": "Confirmation: 2x General Admission tickets for Bukit Jalil National Stadium (Sept 27, 2027). Your e-tickets will be available in the app 7 days before the show.",
    "unsubscribe_url": "https://ticketmaster.com.my/unsubscribe/pref",
    "status": "Unprocessed"
  },
  {
    "id": 11,
    "sender": "KFC Malaysia <orders@kfc.com.my>",
    "subject": "Your KFC Receipt - Order #KFC-99210",
    "body_snippet": "Thank you for your purchase at KFC Subang SS15. Total: RM42.50. This is a confirmation of your order; please keep this for your records.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 12,
    "sender": "McDonald's Malaysia <crm@mcdonalds.com.my>",
    "subject": "The Prosperity Burger is Back! 🍔",
    "body_snippet": "It's that time of year again! Head over to the McD near Sunway Pyramid and grab your favorite black pepper sauce burger today.",
    "unsubscribe_url": "https://unsubscribe.mcdonalds.com.my/token456",
    "status": "Unprocessed"
  },
  {
    "id": 13,
    "sender": "TNB e-Services <bill@tnb.com.my>",
    "subject": "Your Digital Bill for Account ending in 4402",
    "body_snippet": "Your Tenaga Nasional Berhad bill for the period of March-April 2026 is now available. Amount Due: RM145.20. Pay via the myTNB app.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 14,
    "sender": "Maxis <ebilling@maxis.com.my>",
    "subject": "Maxis Postpaid Statement - April 2026",
    "body_snippet": "Hi CHIA XIN YUE, your latest statement is ready for viewing. Total amount due: RM98.00. Thank you for choosing Maxis.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 15,
    "sender": "Texas Chicken <promo@texaschicken.com.my>",
    "subject": "Crunchy Deals! 8-pc Chicken for RM30 🍗",
    "body_snippet": "Why settle for less when you can have the crunchiest chicken in Malaysia? Only available this weekend at all outlets.",
    "unsubscribe_url": "https://texaschicken.com.my/opt-out",
    "status": "Unprocessed"
  },
  {
    "id": 16,
    "sender": "Shopee Malaysia <shipping@shopee.com.my>",
    "subject": "Out for Delivery: Your order for 'Mechanical Keyboard'",
    "body_snippet": "Our courier partner is delivering your package today! Please ensure someone is at home in Subang Jaya to receive it.",
    "unsubscribe_url": "https://shopee.com.my/settings/notifications",
    "status": "Unprocessed"
  },
  {
    "id": 17,
    "sender": "Monash Alumni <alumni@monash.edu>",
    "subject": "Monash Career Fair 2026: Meet Top Tech Employers",
    "body_snippet": "Calling all recent CS graduates! Join us at the Sunway campus to network with companies like Google, Grab, and Petronas.",
    "unsubscribe_url": "https://monash.edu/alumni/unsubscribe",
    "status": "Unprocessed"
  },
  {
    "id": 18,
    "sender": "Uniqlo Malaysia <news@uniqlo.com.my>",
    "subject": "New Arrivals: AIRism Collection 👕",
    "body_snippet": "Stay cool in the Malaysian heat. Check out our latest AIRism arrivals, perfect for working from home or a casual day out.",
    "unsubscribe_url": "https://uniqlo.com.my/unsubscribe/user123",
    "status": "Unprocessed"
  },
  {
    "id": 19,
    "sender": "Grab Malaysia <receipts@grab.com>",
    "subject": "Your trip on Thursday afternoon",
    "body_snippet": "Thanks for riding with us, Xin Yue! Total: RM12.00. Pick up: Monash University Malaysia. Drop off: Subang Jaya SS15.",
    "unsubscribe_url": None,
    "status": "Unprocessed"
  },
  {
    "id": 20,
    "sender": "Eventbrite <noreply@eventbrite.com>",
    "subject": "Reminder: Data Science Workshop starts tomorrow!",
    "body_snippet": "Don't forget your ticket for 'Advanced RAG Architectures'. The session starts at 10:00 AM. See you there!",
    "unsubscribe_url": "https://eventbrite.com/settings/emails",
    "status": "Unprocessed"
  }
]

conn = sqlite3.connect('emails.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS emails 
               (id INTEGER PRIMARY KEY, sender TEXT, subject TEXT, 
                body_snippet TEXT, unsubscribe_url TEXT, status TEXT)''')

for email in mock_data:
    cursor.execute('''INSERT INTO emails VALUES (?, ?, ?, ?, ?, ?)''', 
                   (email['id'], email['sender'], email['subject'], 
                    email['body_snippet'], email['unsubscribe_url'], email['status']))

conn.commit()
conn.close()
print("Database populated.")
