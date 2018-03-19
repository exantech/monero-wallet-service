from models.base import database
from models import Wallet, MultisigInfo
from models.push import PushRegistration

database.evolve(interactive=False)
