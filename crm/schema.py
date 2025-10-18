import re
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

# -----------------------------
# GraphQL Types
# -----------------------------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")

# --- Query Class ---
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, order_by=graphene.String())
    all_products = DjangoFilterConnectionField(ProductType, order_by=graphene.String())
    all_orders = DjangoFilterConnectionField(OrderType, order_by=graphene.String())

    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.all()
        if order_by:
            qs = qs.order_by(order_by)
        return qs



# -----------------------------
# Input Types
# -----------------------------
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# -----------------------------
# Mutations
# -----------------------------
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []
        email = input.email.lower().strip()

        # Email uniqueness check
        if Customer.objects.filter(email=email).exists():
            errors.append("Email already exists")

        # Phone format validation
        if input.phone and not re.match(r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$', input.phone):
            errors.append("Invalid phone number format")

        if errors:
            return CreateCustomer(errors=errors, message="Validation failed")

        customer = Customer.objects.create(
            name=input.name,
            email=email,
            phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for data in input:
            email = data.email.lower().strip()
            if Customer.objects.filter(email=email).exists():
                errors.append(f"Email {email} already exists")
                continue

            if data.phone and not re.match(r'^(\+\d{1,15}|\d{3}-\d{3}-\d{4})$', data.phone):
                errors.append(f"Invalid phone format for {data.name}")
                continue

            customer = Customer(name=data.name, email=email, phone=data.phone)
            created_customers.append(customer)

        # Bulk create valid ones
        Customer.objects.bulk_create(created_customers)
        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        errors = []

        if input.price <= 0:
            errors.append("Price must be positive")
        if input.stock is not None and input.stock < 0:
            errors.append("Stock cannot be negative")

        if errors:
            return CreateProduct(errors=errors, message="Validation failed")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock or 0
        )

        return CreateProduct(product=product, message="Product created successfully")


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        errors = []

        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            errors.append("Invalid customer ID")

        if not input.product_ids:
            errors.append("At least one product must be provided")

        products = Product.objects.filter(id__in=input.product_ids)
        if len(products) != len(input.product_ids):
            errors.append("Some product IDs are invalid")

        if errors:
            return CreateOrder(errors=errors, message="Validation failed")

        total = sum([p.price for p in products])
        order = Order.objects.create(
            customer=customer,
            total_amount=total,
            order_date=input.order_date or timezone.now()
        )
        order.products.set(products)

        return CreateOrder(order=order, message="Order created successfully")


# -----------------------------
# Root Mutation
# -----------------------------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
