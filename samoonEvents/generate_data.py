import random
import string
import lorem
from .app import create_app, db
from .models.user import User
from .models.vendor import Vendor
from .models.review import Review
from werkzeug.security import generate_password_hash


# Generate a weighted random rating
def weighted_starts_rating() -> int:
    return random.choices([1, 2, 3, 4, 5], weights=[0.5, 0.5, 1.5, 2.5, 5])[0]


# generate random password
def generate_random_password(length=10):
    """Generate a random password with letters and digits."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# generate data
def create_data():
    # Create a list of users with hashed passwords
    users_data = [
        {'username': 'John', 'email': "john.doe@example.com"},
        {'username': 'Emily', 'email': "emily.smith@example.com"},
        {'username': 'Michael', 'email': "michael.johnson@example.com"},
        {'username': 'Sarah', 'email': "sarah.williams@example.com"},
        {'username': 'David', 'email': "david.brown@example.com"},
        {'username': 'Jessica', 'email': "jessica.davis@example.com"},
    ]

    # create a list of users
    for user_data in users_data:
        # generate random password
        password = generate_random_password()
        # create new user
        new_user = User(
            username=user_data['username'],
            email=user_data['email'],
        )
        # set the hashed password
        new_user.password = generate_password_hash(password)
        # add user to the database
        db.session.add(new_user)
        # commit the changes
        db.session.commit()
        print(f"Created user: {new_user.username} with password: {password}")

    # This list of categories is used to define the types of vendors in the system.
    # It's referenced when creating vendor data in the vendors_data list below.
    categories = ['Catering', 'Florist', 'Entertainment', 'Photography', 'Venue', 'Bakery', 'Decor']

    # Update vendors_data to use the new categories
    vendors_data = [
        {'name': 'Acme Inc.', 'description': 'A premier catering company for all events.', 'image_path': 'https://images.unsplash.com/photo-1604702433171-33756f3f3825', 'phone_number': '+971566474345', 'email': 'info@acmeltd.co.ke', 'service_fee': 26000, 'category': 'Catering'},
        {'name': 'Floral Studio', 'description': 'Exquisite floral arrangements for your special day.', 'image_path': 'https://images.unsplash.com/reserve/xd45Y326SvKzSR3Nanc8_MRJ_8125-1.jpg', 'phone_number': '+971566474345', 'email': 'hello@floralstudio.com', 'service_fee': 45000, 'category': 'Florist'},
        {'name': 'Rhythm Masters', 'description': 'Top-notch entertainment for unforgettable events.', 'image_path': 'https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3', 'phone_number': '+971566474346', 'email': 'bookings@rhythmmasters.com', 'service_fee': 35000, 'category': 'Entertainment'},
        {'name': 'Capture Moments', 'description': 'Professional photography to preserve your memories.', 'image_path': 'https://images.unsplash.com/photo-1519741497674-611481863552', 'phone_number': '+971566474347', 'email': 'info@capturemoments.com', 'service_fee': 50000, 'category': 'Photography'},
        {'name': 'Grand Plaza', 'description': 'Elegant venue for all your event needs.', 'image_path': 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3', 'phone_number': '+971566474349', 'email': 'bookings@grandplaza.com', 'service_fee': 100000, 'category': 'Venue'},
        {'name': 'Sweet Delights Bakery', 'description': 'Delicious cakes and pastries for every occasion.', 'image_path': 'https://images.unsplash.com/photo-1627580358573-ea0c4a2cb199', 'phone_number': '+971566474348', 'email': 'orders@sweetdelights.com', 'service_fee': 20000, 'category': 'Bakery'},
        {'name': 'Decor Dreams', 'description': 'Transforming spaces into magical settings.', 'image_path': 'https://images.unsplash.com/photo-1501281668745-f7f57925c3b4', 'phone_number': '+971566474346', 'email': 'info@decordreams.com', 'service_fee': 40000, 'category': 'Decor'},
    ]

    for vendor_data in vendors_data:
        print(f"Creating new vendor: {vendor_data['name']}")

        new_vendor = Vendor(**vendor_data)
        db.session.add(new_vendor)
        db.session.commit()

        # Create random reviews
        total_rating = 0
        num_reviews = random.randint(1, 5)
        for _ in range(num_reviews):
            random_user = random.choice(User.query.all())
            print(f"Creating new review for {vendor_data['name']} from {random_user.username}")

            rating = weighted_starts_rating()
            total_rating += rating
            comment = generate_comment(vendor_data['category'], rating)
            review = Review(
                rating=rating,
                comment=comment,
                user=random_user,
                vendor=new_vendor
            )
            db.session.add(review)

        # Calculate and set the overall rating
        if num_reviews > 0:
            new_vendor.rating = round(total_rating / num_reviews, 1)
        else:
            new_vendor.rating = 0.0

        db.session.commit()

    db.session.close()


def generate_comment(category, rating):
    positive_comments = [
        "Great service!",
        "Highly recommended.",
        "Exceeded our expectations.",
        "Made our day special.",
        "Very professional and friendly.",
    ]
    negative_comments = [
        "Disappointed with the service.",
        "Not worth the price.",
        "Could have been better.",
        "Had some issues.",
        "Wouldn't recommend.",
    ]
    neutral_comments = [
        "It was okay.",
        "Average service.",
        "Met our basic needs.",
        "Nothing special, but not bad.",
        "Decent, but room for improvement.",
    ]

    if rating >= 4:
        base_comment = random.choice(positive_comments)
    elif rating <= 2:
        base_comment = random.choice(negative_comments)
    else:
        base_comment = random.choice(neutral_comments)

    return f"{base_comment} {lorem.sentence()}"


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_data()
