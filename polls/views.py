# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.forms import formset_factory, inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.utils.decorators import method_decorator

from accounts.models import WhaleUser
from polls.forms import VotingPollForm, CandidateForm, BaseCandidateFormSet, VotingForm, DateCandidateForm, DateForm
from polls.models import VotingPoll, Candidate, preference_model_from_text, VotingScore, UNDEFINED_VALUE, \
    DateCandidate


# Create your views here.

def home(request):
    return render(request, 'polls/home.html', {})


def success(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    return render(request, 'polls/success.html', {'poll': poll})


class VotingPollMixin(object):
    model = VotingPoll
    form_class = VotingPollForm
    template_name = "polls/votingPoll_form.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(VotingPollMixin, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(manage_candidate, kwargs={'pk': self.object.pk,})

    def form_valid(self, form):
        poll = form.save(commit=False)
        poll.admin = self.request.user
        poll.save()
        return super(VotingPollMixin, self).form_valid(form)


class VotingPollUpdate(VotingPollMixin, UpdateView):
    """
    VotingPollMixin does everything
    """
    pass


class VotingPollCreate(VotingPollMixin, CreateView):
    """
    VotingPollMixin does everything
    """
    pass


def manage_candidate(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    if poll.poll_type != 'Date':
        return redirect(reverse_lazy(candidate_create, kwargs={'pk': poll.id}))
    else:
        return redirect(reverse_lazy(date_candidate_create, kwargs={'pk': poll.id}))


def candidate_create(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    candidateformset = inlineformset_factory(VotingPoll, Candidate,
                                             form=CandidateForm, formset=BaseCandidateFormSet, min_num=2, extra=1,
                                             can_delete=False, validate_min=True)
    if request.method == 'POST':
        formset = candidateformset(request.POST, instance=poll,prefix='form')
        if formset.is_valid():
            formset.save()
            messages.success(request, _('Candidates successfully added!'))
            return redirect(reverse_lazy(success, kwargs={'pk': poll.id}))
    else:
        formset = candidateformset(instance=poll,prefix='form')
    return render(request, 'polls/candidate_form.html', {'formset': formset, 'poll': poll})


def date_candidate_create(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    date_candidateformset = inlineformset_factory(VotingPoll, DateCandidate,
                                             form=DateCandidateForm, formset=BaseCandidateFormSet, extra=1,
                                             can_delete=False)
    if request.method == 'POST':
        form = DateForm(request.POST)
        formset = date_candidateformset(request.POST, instance=poll,prefix='form')
        if form.is_valid():
            dates = form.cleaned_data['dates']
            if formset.is_valid():
                print(formset)
                label = formset.save(commit=False)
                for date in dates:
                    for c in label:
                        c.date=date
                        c.save()
                messages.success(request, _('Candidates successfully added!'))
                return redirect(reverse_lazy(date_candidate_create, kwargs={'pk': poll.pk}))
    else:
        formset = date_candidateformset(prefix='form')
        form = DateForm()
        candidates=DateCandidate.objects.filter(poll_id=poll.id)

    return render(request, 'polls/candidate2.html',
                  {'formset': formset,'form':form, 'poll': poll, 'candidates':candidates})


def delete_candidate(request, pk, cand):
    poll = get_object_or_404(VotingPoll, id=pk)
    candidate = get_object_or_404(DateCandidate, id=cand)
    candidate.delete()
    return redirect(reverse_lazy(date_candidate_create, kwargs={'pk': poll.id}))


def with_admin_rights(fn):
    def wrapped(request, pk):
        next = request.get_full_path()
        poll = get_object_or_404(VotingPoll, id=pk)
        if request.user is None or request.user != poll.admin:
            return redirect('/accounts/login?next={next}'.format(next=next))
        return fn(request,pk)
    return wrapped


@with_admin_rights
def admin_poll(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    return redirect(reverse_lazy(manage_candidate, kwargs={'pk': poll.pk,}))


def vote(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    candidates = (
        DateCandidate.objects.filter(poll_id=poll.id) if poll.poll_type == 'Date'else Candidate.objects.filter(
            poll_id=poll.id))
    preference_model = preference_model_from_text(poll.preference_model)
    months = []
    days = []
    if request.user.is_authenticated():
        initial = {'nickname': request.user.nickname}
        voter=request.user
        read=True
    else:
        initial = {}
        read=False
        users = WhaleUser.objects.count() + 1
        email = 'whale4' + str(users) + '@gmail.com'
        voter = WhaleUser.objects.create_user(
        email=email,
        nickname='',
        password='whale4')

    if poll.poll_type == 'Date':
        (days, months) = days_month(candidates)

    if request.method == 'POST':
        form = VotingForm(candidates, preference_model,poll,read,request.POST)

        if form.is_valid():
            data = form.cleaned_data
            voter.nickname = data['nickname']
            voter.save()
            for c in candidates:
                VotingScore.objects.create(candidate=c, voter=voter, value=data['value' + str(c.id)])
            return redirect(reverse_lazy(view_poll, kwargs={'pk': poll.pk}))
    else:

        form = VotingForm(candidates, preference_model,poll,read,initial=initial)

    return render(request, 'polls/vote.html', {'form': form, 'poll': poll, 'months': months, 'days': days})


def update_vote(request, pk, voter):
    poll = VotingPoll.objects.get(id=pk)
    candidates = (
        DateCandidate.objects.filter(poll_id=poll.id) if poll.poll_type == 'Date'else Candidate.objects.filter(
            poll_id=poll.id))
    preference_model = preference_model_from_text(poll.preference_model)
    voter = WhaleUser.objects.get(id=voter)
    votes = VotingScore.objects.filter(candidate__poll__id=poll.id).filter(voter=voter.id)
    initial = {}
    initial['nickname'] = voter.nickname
    for v in votes:
        initial['value' + str(v.candidate.id)] = v.value

    if request.user.is_authenticated():

        read = True
    else:

        read = False
    if request.method == 'POST':
        form = VotingForm(candidates, preference_model,poll,read, request.POST)

        if form.is_valid():
            data = form.cleaned_data
            voter.nickname = data['nickname']
            voter.save()
            for v in votes:
                v.value = data['value' + str(v.candidate.id)]
                v.save()
            return redirect(reverse_lazy(view_poll, kwargs={'pk': poll.pk}))
    else:
        form = VotingForm(candidates, preference_model,poll,read, initial=initial)

    return render(request, 'polls/vote.html', {'form': form, 'poll': poll})


def delete_vote(request, pk, voter):
    poll = VotingPoll.objects.get(id=pk)
    voter = WhaleUser.objects.get(id=voter)
    votes = VotingScore.objects.filter(candidate__poll__id=poll.id).filter(voter=voter.id)

    if request.method == 'POST':
        votes.delete()
        voter.delete()
        return redirect(reverse_lazy(view_poll, kwargs={'pk': poll.pk}))
    return render(request, 'polls/delete_vote.html', {'voter': voter, 'poll': poll})


def days_month(candidates):
    months = []
    days = []
    for c in candidates:
        current_month = c.date.strftime("%y/%m")
        current_day = c.date.strftime("%y/%m/%d")
        if len(months) > 0 and months[-1]["label"] == current_month:
            months[-1]["value"] += 1
        else:
            months += [{"label": current_month, "value": 1}]
        if len(days) > 0 and days[-1]["label"] == current_day:
            days[-1]["value"] += 1
        else:
            days += [{"label": current_day, "value": 1}]
    return (days, months)


def view_poll(request, pk):
    poll = get_object_or_404(VotingPoll, id=pk)
    candidates = (
        DateCandidate.objects.filter(poll_id=poll.id) if poll.poll_type == 'Date'else Candidate.objects.filter(
            poll_id=poll.id))
    votes = VotingScore.objects.filter(candidate__poll__id=poll.id)
    preference_model = preference_model_from_text(poll.preference_model)
    months = []
    days = []
    if poll.poll_type == 'Date':
        (days, months) = days_month(candidates)
    scores = {}
    for v in votes:
        if v.voter.id not in scores:
            scores[v.voter.id] = {}
        scores[v.voter.id][v.candidate.id] = v.value
    print(scores)
    tab = {}
    for v in votes:
        id = v.voter.id
        tab[id] = {}
        tab[id]['id'] = id
        tab[id]['nickname'] = v.voter.nickname
        tab[id]['scores'] = []
        for c in candidates:
            if c.id in scores[id]:
                score = scores[id][c.id]
                tab[id]['scores'].append({
                    'value': score,
                    'class': 'poll-{0:d}percent'.format(int(round(preference_model.evaluate(score),
                                                                  1) * 100)) if score != UNDEFINED_VALUE else 'poll-undefined',
                    'text': preference_model.value2text(score) if score != UNDEFINED_VALUE else "?"
                })

    values = None if tab == {} else tab.values()

    return render(request, 'polls/viewPoll.html',
                  {'poll': poll, 'candidates': candidates, 'votes': values, 'months': months, 'days': days})


def bad_request(request):
    response = render_to_response('polls/400.html', {}, context_instance=RequestContext(request))
    response.status_code = 400
    return response


def permission_denied(request):
    response = render_to_response('polls/403.html', {}, context_instance=RequestContext(request))
    response.status_code = 403
    return response


def page_not_found(request):
    response = render_to_response('polls/404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response


def server_error(request):
    response = render_to_response('polls/500.html', {}, context_instance=RequestContext(request))
    response.status_code = 500
    return response
