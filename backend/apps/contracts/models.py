from django.db import models


class CorporateAccount(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="corporate_accounts")
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=80, blank=True)
    billing_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("hotel", "name")]

    def __str__(self):
        return self.name


class CorporateContract(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="corporate_contracts")
    corporate = models.ForeignKey(CorporateAccount, on_delete=models.PROTECT, related_name="contracts")
    contract_code = models.CharField(max_length=60)
    start_date = models.DateField()
    end_date = models.DateField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    rate_plan_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("hotel", "contract_code")]

    def __str__(self):
        return f"{self.contract_code} ({self.corporate})"


class Agent(models.Model):
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="agents")
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("hotel", "name")]

    def __str__(self):
        return self.name


class CommissionRule(models.Model):
    """
    Real-life: agents/OTAs get commission rules.
    Later you can connect this to reservations source/channel.
    """
    hotel = models.ForeignKey("tenants.Hotel", on_delete=models.CASCADE, related_name="commission_rules")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="commission_rules")
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("hotel", "agent")]

    def __str__(self):
        return f"{self.agent} {self.percent}%"
