import csv
import numpy as np

user_set = set()
item_set = set()

user_rate_list = {}  # map (uid) -> [(iid,rating,loc,time)]
user_rate_list_ground_truth = {}  # map (uid) -> [(iid,rating,loc,time)]

def cosine_sim(user_1, user_2, time='ANY', location='ANY'):
    """
    cosine similarity between users using pre-filtering
    :return: a float : score
    """

    score_1 = {}
    score_2 = {}
    N1 = 0
    N2 = 0
    N = 0
    for item in user_rate_list[user_1]:
        if (time == 'ANY' or time == item[2]) and (location == 'ANY' or location == item[3]):
            score_1[item[0]] = int(item[1])
    for item in user_rate_list[user_2]:
        if (time == 'ANY' or time == item[2]) and (location == 'ANY' or location == item[3]):
            score_2[item[0]] = int(item[1])

    # in case of duplication:
    for id in score_1:
        N1 += score_1[id] * score_1[id]
    for id in score_2:
        N2 += score_2[id] * score_2[id]

    # calculate cosine
    for id in score_1:
        if score_2.has_key(id):
            N += score_1[id] * score_2[id]
            # print id, score_1[id], score_2[id]
    if N1 == 0 or N2 == 0:
        return 0
    return N / (np.sqrt(N1) * np.sqrt(N2))


def recommend(user, time='ANY', location='ANY'):
    """
    recommendation algorithm with pre-filtering
    :param user: user id
    :param time: ANY or a time
    :param location: ANY or a location
    :return: list of (recommendation item, score)
    """
    sum = 0
    for other_user in user_rate_list:
        if user == other_user:
            continue
        sum += cosine_sim(user, other_user,time,location)

    score_final = {} # = sum{score/count}
    for other_user in user_rate_list:
        if user == other_user:
            continue
        k = cosine_sim(user, other_user, time, location) / sum

         # average when user has more than one rating for an item
        score = {}
        count = {}

        for item in user_rate_list[other_user]:
            # pre filtering
            if (time == 'ANY' or time == item[2]) and (location == 'ANY' or location == item[3]):
                id = item[0]
                rate = float(item[1])
                # if id == 'tt0266543':
                #     print other_user, k * rate,rate, k,k*sum,sum
                if score.has_key(id):
                    score[id] += k * rate
                    count[id] += 1
                else:
                    score[id] = k * rate
                    count[id] = 1
        for id in score:
            if score_final.has_key(id):
                score_final[id] += score[id]/count[id]
            else:
                score_final[id] = score[id]/count[id]

    # filter out items
    viewed = {}
    for item in user_rate_list[userid]:
        viewed[item[0]] = 1


    # sorting
    result = []
    for id in score_final:
        if not viewed.has_key(id):
            result.append((id, score_final[id]))

    result.sort(key=lambda x: x[1], reverse=True)
    return result

# main
if __name__ == '__main__':

    with open('frappe.txt', 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')

        for row in reader:
            location = row['homework']
            time = row['daytime']
            userid = row['user']
            itemid = row['item']
            rating = row['cnt']
            user_set.add(userid)
            item_set.add(itemid)

            ignore_flag = 0
            if np.random.random()<0.5:
                ignore_flag = 1

            # only use data where time and location are both available
            if location != 'NA' and time != 'NA':
                if ignore_flag == 0:
                    if user_rate_list.has_key(userid):
                        user_rate_list[userid].append((itemid, rating, time, location))
                    else:
                        user_rate_list[userid] = [(itemid, rating, time, location)]
                else:
                    if user_rate_list_ground_truth.has_key(userid):
                        user_rate_list_ground_truth[userid].append((itemid, rating, time, location))
                    else:
                        user_rate_list_ground_truth[userid] = [(itemid, rating, time, location)]

    print 'user count =',len(user_set)
    print 'item count =',len(item_set)


    # recommendation
    target_user = '10'
    result = recommend(target_user)

    # evaluation
    user_ratings = user_rate_list_ground_truth[target_user]
    user_ratings.sort(key=lambda x: int(x[1]), reverse=True)

    user_ratings = map(lambda x: (x[0],int(x[1])), user_ratings)
    ground_truth = {}
    for item in user_ratings:
        if ground_truth.has_key(item[0]):
            ground_truth[item[0]] += item[1]
        else:
            ground_truth[item[0]] = item[1]


    print "==================================="
    print "item, recommended_score, real_score"
    print "------------------------------------"
    cnt = 0
    score = 0
    for item in result:
        # CG
        if ground_truth.has_key(item[0]):
            item_score = ground_truth[item[0]]
        else:
            item_score = 0
        # DCG
        if cnt != 0:
            item_score /= np.log2(cnt+1)
        print item, item_score
        cnt = cnt+1
        score += item_score
        # top 10 DCG
        if cnt == 10:
            break

    max_DCG = sorted(ground_truth.values(),reverse=True)
    print "==================================="
    print "recommendation result:",result
    print "ground truth:",ground_truth
    print "Sorted ground truth(to compute max possible DCG):",max_DCG
    #NDCG
    print "nDCG =",score/sum(max_DCG[0:cnt])


