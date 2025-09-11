from app.models.model import DealershipAddress

def get_dealership_address(dealership_id: str) -> DealershipAddress:
    """
    Mock dealership address retrieval
    """
    # dealerships = {
    #     "NYC01": DealershipAddress(
    #         dealership_id="NYC01", 
    #         name="SuperCar Manhattan", 
    #         address="123 Broadway, New York, NY 10001",
    #         phone="(212) 555-1234"
    #     ),
    #     "LA01": DealershipAddress(
    #         dealership_id="LA01", 
    #         name="SuperCar Los Angeles", 
    #         address="456 Sunset Blvd, Los Angeles, CA 90028",
    #         phone="(323) 555-5678"
    #     )
    # }
    # return dealerships.get(dealership_id, 
    #     DealershipAddress(
    #         dealership_id=dealership_id, 
    #         name="Unknown Dealership", 
    #         address="Address Not Found"
    #     )
    # )

    dealerships = {
        "NYC01": {
            "dealership_id": "NYC01", 
            "name": "SuperCar Manhattan", 
            "address": "123 Broadway, New York, NY 10001",
            "phone" : "(212) 555-1234",
            "hours":"24 hours"
        },
        "LA01":{
            "dealership_id": "LA01", 
            "name": "SuperCar Los Angeles", 
            "address": "456 Sunset Blvd, Los Angeles, CA 90028",
            "phone": "(323) 555-5678",
            "hours":"24 hours"
        }
        }
    return dealerships.get(dealership_id)