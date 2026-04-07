"""Seed script — populates the databases with realistic test data.

Run with: make seed
Creates ~50 records across listings, calendar events, and inbox messages
so the agent has data to work with during interactive testing.
"""

from datetime import datetime, timedelta

from backend.inbox_manager import InboxManager
from backend.calendar_manager import CalendarManager
from backend.listings_manager import ListingsManager


def seed_listings(listings: ListingsManager):
    data = [
        ("Spacious 2BR apartment with balcony in downtown", "123 Oak Street", 2500, 2, 2),
        ("Cozy 2BR apartment near Riverside Park", "456 Maple Ave", 2800, 2, 1),
        ("Luxury 2BR with panoramic city views", "789 Pine Road", 3500, 2, 2),
        ("Studio apartment in downtown arts district", "321 Elm Street", 1800, 1, 1),
        ("Modern 3BR townhouse with garage", "550 Cedar Lane", 3200, 3, 2),
        ("Renovated 1BR with in-unit laundry", "88 Birch Court", 2100, 1, 1),
        ("Charming 2BR cottage with garden", "12 Willow Way", 2600, 2, 1),
        ("Penthouse 3BR with rooftop terrace", "900 Summit Ave", 4500, 3, 3),
        ("Affordable 1BR near university campus", "201 College Blvd", 1500, 1, 1),
        ("Spacious 4BR family home with yard", "77 Oakwood Drive", 3800, 4, 3),
        ("Loft-style 1BR in converted warehouse", "15 Industrial Way", 2200, 1, 1),
        ("Pet-friendly 2BR with fenced yard", "340 Meadow Lane", 2400, 2, 1),
        ("Bright corner 3BR with bay windows", "610 Harbor View", 3100, 3, 2),
        ("Newly built 2BR with smart home features", "425 Tech Park Dr", 2900, 2, 2),
        ("Cozy studio above Main Street shops", "100 Main Street", 1600, 1, 1),
    ]
    for desc, addr, rent, beds, baths in data:
        listings.create_listing(
            description=desc,
            address=addr,
            monthly_rent=rent,
            bedrooms=beds,
            bathrooms=baths,
        )
    print(f"  Created {len(data)} listings")


def seed_calendar(calendar: CalendarManager):
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    day_after = now + timedelta(days=2)
    next_week = now + timedelta(days=7)

    events = [
        # Tomorrow
        ("Showing at 123 Oak Street", tomorrow.replace(hour=10, minute=0), tomorrow.replace(hour=11, minute=0),
         ["sarah.jones@example.com"]),
        ("Showing at 456 Maple Ave", tomorrow.replace(hour=13, minute=0), tomorrow.replace(hour=14, minute=0),
         ["mike.chen@example.com"]),
        ("Client meeting — lease signing", tomorrow.replace(hour=15, minute=0), tomorrow.replace(hour=16, minute=0),
         ["alex.rivera@example.com"]),
        ("Showing at 550 Cedar Lane", tomorrow.replace(hour=16, minute=30), tomorrow.replace(hour=17, minute=30),
         ["priya.patel@example.com"]),
        # Day after tomorrow
        ("Property inspection at 789 Pine Road", day_after.replace(hour=9, minute=0), day_after.replace(hour=10, minute=0),
         ["inspector@cityinspections.com"]),
        ("Showing at 12 Willow Way", day_after.replace(hour=11, minute=0), day_after.replace(hour=12, minute=0),
         ["emma.wilson@example.com"]),
        ("Maintenance walkthrough at 321 Elm Street", day_after.replace(hour=14, minute=0), day_after.replace(hour=15, minute=0),
         ["bob@fixitplumbing.com"]),
        ("Showing at 88 Birch Court", day_after.replace(hour=16, minute=0), day_after.replace(hour=17, minute=0),
         ["james.lee@example.com"]),
        # Next week
        ("Open house at 900 Summit Ave", next_week.replace(hour=10, minute=0), next_week.replace(hour=13, minute=0),
         ["sarah.jones@example.com", "mike.chen@example.com", "emma.wilson@example.com"]),
        ("Contractor meeting — 77 Oakwood Drive renovation", next_week.replace(hour=14, minute=0), next_week.replace(hour=15, minute=0),
         ["dan@premiumbuilders.com"]),
        ("Showing at 610 Harbor View", (next_week + timedelta(days=1)).replace(hour=11, minute=0),
         (next_week + timedelta(days=1)).replace(hour=12, minute=0), ["olivia.garcia@example.com"]),
        ("Lease renewal discussion", (next_week + timedelta(days=2)).replace(hour=10, minute=0),
         (next_week + timedelta(days=2)).replace(hour=11, minute=0), ["current.tenant@example.com"]),
    ]
    for name, start, end, guests in events:
        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)
        calendar.create_event(
            name=name,
            start_timestamp=start,
            end_timestamp=end,
            guests=guests,
        )
    print(f"  Created {len(events)} calendar events")


def seed_inbox(inbox: InboxManager):
    # Incoming emails
    incoming = [
        ("sarah.jones@example.com", "Apartment inquiry",
         "Hi, I'm looking for a 2 bedroom apartment under $3000. What do you have available?"),
        ("mike.chen@example.com", "Viewing request",
         "I'd like to schedule a viewing at 456 Maple Ave. Is tomorrow afternoon available?"),
        ("alex.rivera@example.com", "Lease question",
         "I'm interested in the 3BR townhouse at 550 Cedar Lane. What's the lease term?"),
        ("priya.patel@example.com", "Pet policy",
         "Does the property at 340 Meadow Lane allow large dogs? I have a golden retriever."),
        ("emma.wilson@example.com", "Cancellation request",
         "I need to cancel my showing at 12 Willow Way. I found another place. Thanks!"),
        ("james.lee@example.com", "Move-in date",
         "If I sign for 88 Birch Court, what's the earliest move-in date?"),
        ("olivia.garcia@example.com", "Parking question",
         "Does 610 Harbor View come with a parking spot? I have two cars."),
        ("current.tenant@example.com", "Maintenance request",
         "The kitchen faucet in my unit at 321 Elm Street has been leaking. Can someone take a look?"),
        ("sarah.jones@example.com", "Follow up",
         "Thanks for showing me 123 Oak Street today. I'd like to move forward with an application."),
        ("bob@fixitplumbing.com", "Estimate for 321 Elm",
         "Here's the estimate for the faucet repair at 321 Elm Street: $150 parts + $100 labor. Let me know."),
        ("dan@premiumbuilders.com", "Renovation timeline",
         "The 77 Oakwood Drive renovation should be done in 3 weeks. I'll send photos of progress Friday."),
        ("inspector@cityinspections.com", "Inspection confirmation",
         "Confirming the property inspection at 789 Pine Road for day after tomorrow at 9 AM."),
    ]
    for sender, subject, body in incoming:
        inbox.receive_email(sender=sender, subject=subject, body=body)

    # Outgoing emails
    outgoing = [
        ("sarah.jones@example.com", "Re: Apartment inquiry",
         "Hi Sarah, we have two 2BR apartments under $3000: 123 Oak Street ($2500) and 456 Maple Ave ($2800). Would you like to schedule viewings?"),
        ("mike.chen@example.com", "Re: Viewing request",
         "Hi Mike, I've scheduled you for a viewing at 456 Maple Ave tomorrow at 1 PM. See you there!"),
        ("alex.rivera@example.com", "Re: Lease question",
         "Hi Alex, the lease at 550 Cedar Lane is 12 months with an option to renew. First month + security deposit required."),
        ("priya.patel@example.com", "Re: Pet policy",
         "Hi Priya, 340 Meadow Lane is pet-friendly with no breed restrictions. There's a $500 pet deposit. Would you like to see it?"),
        ("current.tenant@example.com", "Re: Maintenance request",
         "Hi, I've scheduled a plumber to look at the faucet. They'll be at your unit day after tomorrow at 2 PM."),
        ("bob@fixitplumbing.com", "Re: Estimate for 321 Elm",
         "That works. Please go ahead with the repair. The tenant will be home day after tomorrow at 2 PM."),
        ("emma.wilson@example.com", "Re: Cancellation request",
         "No problem, Emma. I've cancelled your showing at 12 Willow Way. Good luck with your new place!"),
        ("james.lee@example.com", "Re: Move-in date",
         "Hi James, the earliest move-in for 88 Birch Court is the 1st of next month. Let me know if you'd like to proceed."),
    ]
    for recipient, subject, body in outgoing:
        inbox.send_email(recipient=recipient, subject=subject, body=body)

    print(f"  Created {len(incoming)} incoming + {len(outgoing)} outgoing emails")


def wipe_databases():
    """Remove existing database files so seeding starts fresh."""
    import os
    for db in ("inbox.db", "calendar.db", "listings.db"):
        if os.path.exists(db):
            os.remove(db)


def main():
    wipe_databases()
    print("Seeding databases...")
    seed_listings(ListingsManager())
    seed_calendar(CalendarManager())
    seed_inbox(InboxManager())
    print("Done! Databases ready for testing.")


if __name__ == "__main__":
    main()
