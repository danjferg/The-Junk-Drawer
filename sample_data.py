from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# List for Packing List
category1 = Category(user_id=1, name="Packing List")

session.add(category1)
session.commit()

listItem2 = Item(user_id=1, name="Pants", description="Need to pack two pairs",
                     category=category1)

session.add(listItem2)
session.commit()


listItem1 = Item(user_id=1, name="Shirts", description="Pack two shirts.",
                     category=category1)

session.add(listItem1)
session.commit()

listItem2 = Item(user_id=1, name="Hygiene Kit", description="Toothbrush, toothpaste, comb, razor, deodorant and hair gel.",
                     category=category1)

session.add(listItem2)
session.commit()

listItem3 = Item(user_id=1, name="Identification", description="Passport, Driver's License, cash and credit card.",
                     category=category1)

session.add(listItem3)
session.commit()

listItem4 = Item(user_id=1, name="Under Garments", description="Socks, and underwear, three sets.",
                     category=category1)

session.add(listItem4)
session.commit()

listItem5 = Item(user_id=1, name="Jacket", description="For potentially rainy weather.",
                     category=category1)

session.add(listItem5)
session.commit()


print "added list items!"
