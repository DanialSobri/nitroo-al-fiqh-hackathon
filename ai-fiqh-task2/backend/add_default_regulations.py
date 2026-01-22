import requests
import json

BASE_URL = "http://localhost:8000"

default_regulations = [
    {
        "title": "Prohibition of Riba (Interest)",
        "content": """Riba (interest) is strictly prohibited in Islam. This includes:
1. Any fixed return on loans or deposits regardless of the name used (interest, fee, service charge)
2. Interest rates, APR (Annual Percentage Rate), or any percentage-based charges on principal
3. Late payment penalties that include interest components
4. Compounding interest or interest on interest
5. Any predetermined excess over the principal amount in loan agreements
The contract must be free from any form of interest-based transactions. All financing must be based on profit-sharing, leasing, or trade-based structures.""",
        "category": "Financial Prohibition",
        "reference": "Quran 2:275-279, Hadith Bukhari 5764"
    },
    {
        "title": "Prohibition of Gharar (Excessive Uncertainty)",
        "content": """Gharar refers to excessive uncertainty, ambiguity, or deception in contracts. Prohibited elements include:
1. Uncertain delivery dates or quantities
2. Selling items not yet in possession
3. Ambiguous terms that can be interpreted differently
4. Hidden information about the subject matter
5. Speculative transactions where outcomes are highly uncertain
Contracts must have clear terms, defined subject matter, and transparent conditions.""",
        "category": "Contract Clarity",
        "reference": "Hadith Muslim 1513"
    },
    {
        "title": "Prohibition of Maysir (Gambling)",
        "content": """Maysir encompasses gambling and games of chance. This includes:
1. Transactions where gain or loss depends on uncertain events
2. Speculative derivatives without underlying assets
3. Lottery-style arrangements
4. Zero-sum games where one party's gain is another's loss
All transactions must involve real economic activity and tangible value exchange.""",
        "category": "Financial Prohibition",
        "reference": "Quran 5:90-91"
    },
    {
        "title": "Asset-Backing Requirement",
        "content": """Islamic finance requires real asset backing. Contracts must:
1. Be backed by tangible assets or services
2. Involve real economic activity, not just paper transactions
3. Have identifiable underlying assets
4. Reflect genuine trade or investment in productive activities
Money cannot be traded for money without tangible goods or services involved.""",
        "category": "Asset Requirements",
        "reference": "Islamic Finance Principles"
    },
    {
        "title": "Prohibition of Haram Activities",
        "content": """Financing cannot be provided for activities prohibited in Islam:
1. Alcohol production or sale
2. Gambling establishments
3. Pork-related businesses
4. Adult entertainment
5. Conventional interest-based banking
6. Weapons manufacturing for unlawful purposes
The contract must ensure funds are not used for any prohibited purposes.""",
        "category": "Ethical Compliance",
        "reference": "Quran 5:90, 2:173"
    },
    {
        "title": "Risk Sharing Principle",
        "content": """Islamic finance emphasizes risk and profit sharing:
1. Both parties must share in the risk of the venture
2. Guaranteed returns without risk participation are not allowed
3. One party cannot bear all losses while the other takes all profits
4. Profit and loss sharing must be predetermined and clearly stated
5. The financier must participate in the risk of the business activity""",
        "category": "Risk Management",
        "reference": "Islamic Financial Jurisprudence"
    },
    {
        "title": "Transparency and Disclosure",
        "content": """All contract terms must be transparent and fully disclosed:
1. All fees, charges, and costs must be clearly stated upfront
2. No hidden charges or surprise fees
3. Terms must be in clear, understandable language
4. All parties must have full knowledge of contract conditions
5. Material information cannot be withheld from any party""",
        "category": "Contract Integrity",
        "reference": "Hadith on Fair Dealing"
    }
]

def add_regulations():
    print("Adding Shariah regulations to the system...\n")
    
    for reg in default_regulations:
        try:
            response = requests.post(
                f"{BASE_URL}/regulations/add",
                json=reg
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Added: {reg['title']}")
                print(f"  ID: {result['id']}\n")
            else:
                print(f"✗ Failed to add: {reg['title']}")
                print(f"  Error: {response.text}\n")
        except Exception as e:
            print(f"✗ Error adding {reg['title']}: {str(e)}\n")
    
    print("\nDone! All regulations have been added to the database.")

if __name__ == "__main__":
    add_regulations()
