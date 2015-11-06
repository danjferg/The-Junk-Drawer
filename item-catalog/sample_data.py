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


# Create admin user
User1 = User(name="Foobar", email="foobar@foobar.com")

session.add(User1)
session.commit()

# Packing List Category
category1 = Category(user=User1, name="Packing List")

session.add(category1)
session.commit()

listItem1 = Item(name="Pants", description="Need to pack two pairs",
                 category=category1)

session.add(listItem1)
session.commit()

listItem2 = Item(name="Shirts", description="Pack two shirts.",
                 category=category1)

session.add(listItem2)
session.commit()

listItem3 = Item(name="Hygiene Kit",
                 description="Toothbrush, toothpaste, comb, razor, \
                    deodorant and hair gel.",
                 category=category1)

session.add(listItem3)
session.commit()

listItem4 = Item(name="Identification",
                 description="Passport, Driver's License, cash and credit \
                 card.",
                 category=category1)

session.add(listItem4)
session.commit()

listItem5 = Item(name="Under Garments",
                 description="Socks, and underwear, three sets.",
                 category=category1)

session.add(listItem5)
session.commit()

listItem6 = Item(name="Jacket", description="For potentially rainy weather.",
                 category=category1)

session.add(listItem6)
session.commit()


# Spaghetti Recipe Category
category2 = Category(user=User1, name="Spaghetti Recipe")

session.add(category2)
session.commit()

listItem7 = Item(name="Spaghetti Noodles", description="12 oz cooked",
                 picture="Spaghetti Recipe_Spaghetti Noodles.jpg",
                 category=category2)

session.add(listItem7)
session.commit()

listItem8 = Item(name="Spaghetti Sauce", description="16 oz.",
                 picture="Spaghetti Recipe_Spaghetti Sauce.jpg",
                 category=category2)

session.add(listItem8)
session.commit()


print "added list items!"
